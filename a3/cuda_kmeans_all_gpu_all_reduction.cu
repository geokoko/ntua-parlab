#include <stdio.h>
#include <stdlib.h>

#include "kmeans.h"
#include "alloc.h"
#include "error.h"

#ifdef __CUDACC__
inline void checkCuda(cudaError_t e) {
	if (e != cudaSuccess) {
		// cudaGetErrorString() isn't always very helpful. Look up the error
		// number in the cudaError enum in driver_types.h in the CUDA includes
		// directory for a better explanation.
		error("CUDA Error %d: %s\n", e, cudaGetErrorString(e));
	}
}

inline void checkLastCudaError() {
	checkCuda(cudaGetLastError());
}
#endif

__device__ int get_tid() {
	/* Calculate 1-Dim global ID of a thread */
	return blockDim.x * blockIdx.x + threadIdx.x;
}

/* square of Euclid distance between two multi-dimensional points using column-base format */
__host__ __device__ inline static
double euclid_dist_2_transpose(int numCoords,
		int numObjs,
		int numClusters,
		double *objects,     // [numCoords][numObjs]
		double *clusters,    // [numCoords][numClusters]
		int objectId,
		int clusterId) {
	int i;
	double ans = 0.0;

	for (i = 0; i < numCoords; i++) {
		double diff = objects[i * numObjs + objectId] - clusters[i * numClusters + clusterId];
		ans += diff * diff;
	}

	return (ans);
}

template <typename T>
__global__ static
void reduce_blocks(const T *block_data, T *out, int numBlocks, int elemsPerBlock) {
	int idx = blockIdx.x * blockDim.x + threadIdx.x;

	if (idx >= elemsPerBlock) {
		return;
	}

	T sum = 0;
	for (int b = 0; b < numBlocks; ++b) {
		sum += block_data[b * elemsPerBlock + idx];
	}
	out[idx] = sum;
}

/*----< find_nearest_cluster() >---------------------------------------------*/
__global__ static
void find_nearest_cluster(int numCoords,
		int numObjs,
		int numClusters,
		double *deviceobjects,           //  [numCoords][numObjs]
		double *deviceClusters,    //  [numCoords][numClusters]
		double *devicenewClustersBlocks,    //  [numBlocks][numCoords][numClusters]
		int *devicenewClusterSizeBlocks,    //  [numBlocks][numClusters]
		int *deviceMembership,          //  [numObjs]
		double *devdeltaBlocks) { // [numBlocks]
	extern __shared__ double shmem_total[];
	double *shmemClusters = shmem_total;
	double *delta_reduce_buff = shmem_total + numClusters * numCoords;
	int *shmemClusterSizes = (int *)(delta_reduce_buff + blockDim.x);
	int i;
	for (i = threadIdx.x; i < numClusters * numCoords; i += blockDim.x) {
		shmemClusters[i] = deviceClusters[i];
	}
	__syncthreads();

	/* Get the global ID of the thread. */
	int tid = get_tid();
	int index = 0;
	double dist, min_dist;
	double local_delta = 0.0;

	/* Find nearest cluster center for this object */
	if (tid < numObjs) {
		min_dist = euclid_dist_2_transpose(numCoords, numObjs, numClusters, deviceobjects, shmemClusters, tid, 0);

		for (i = 1; i < numClusters; i++) {
			dist = euclid_dist_2_transpose(numCoords, numObjs, numClusters, deviceobjects, shmemClusters, tid, i);
			if (dist < min_dist) {
				min_dist = dist;
				// index = new cluster id
				index = i;
			}
		}
	}

	/* DONE: Replacing (*devdelta)+= 1.0; with reduction:
	   - each thread updates the single element of delta_reduce_buff
	   corresponding to its local id (threadIdx.x) -> 1.0 if membership changes, otherwise 0.
	   - Then, ensuring delta_reduce_buff is fully updated, its containts must be summed in delta_reduce_buff[0]
	   either by one thread (lower perf) or with a tree-based reduction (similar to dot reduction example in slides)
	   - Finally, delta_reduce_buff[0] (local value in block) is written to devdeltaBlocks[blockIdx.x],
	   and a separate reduction kernel combines block results (no global atomics here).
	   */

	/* Assign the cluster to object, and update new cluster centers */
	if (tid < numObjs) {
		int prev = deviceMembership[tid];
		if (prev != index) {
			local_delta = 1.0;
		}
		deviceMembership[tid] = index;
	}

	delta_reduce_buff[threadIdx.x] = local_delta;

	// Ensure all threads have updated their delta buffer
	__syncthreads();

	// Perform tree-based reduction in shared memory per block
	for (int offset = blockDim.x / 2; offset > 0; offset >>= 1) {
		if (threadIdx.x < offset) {
			delta_reduce_buff[threadIdx.x] += delta_reduce_buff[threadIdx.x + offset];
		}
		__syncthreads();
	}
	// everything in every block is now summed to index 0 of delta_reduce_buff
	// No global atomics: each block stores its delta in its own slot.
	if (threadIdx.x == 0) {
		devdeltaBlocks[blockIdx.x] = delta_reduce_buff[0];
	}

	for (i = threadIdx.x; i < numClusters; i += blockDim.x) {
		shmemClusterSizes[i] = 0;
	}
	__syncthreads();

	for (i = threadIdx.x; i < numClusters * numCoords; i += blockDim.x) {
		shmemClusters[i] = 0.0;
	}
	__syncthreads();

	if (tid < numObjs) {
		atomicAdd(&shmemClusterSizes[index], 1);
		for (i = 0; i < numCoords; i++) {
			atomicAdd(&shmemClusters[i * numClusters + index],
					deviceobjects[i * numObjs + tid]);
		}
	}

	__syncthreads();
	/* No global atomics: each block writes its own slice. */
	for (i = threadIdx.x; i < numClusters * numCoords; i += blockDim.x) {
		devicenewClustersBlocks[blockIdx.x * (numClusters * numCoords) + i] = shmemClusters[i];
	}
	for (i = threadIdx.x; i < numClusters; i += blockDim.x) {
		devicenewClusterSizeBlocks[blockIdx.x * numClusters + i] = shmemClusterSizes[i];
	}
}

	__global__ static
void update_centroids(int numCoords,
		int numClusters,
		int *devicenewClusterSize,           //  [numClusters]
		double *devicenewClusters,    //  [numCoords][numClusters]
		double *deviceClusters)    //  [numCoords][numClusters])
{
	int tid = get_tid();
	int total = numCoords * numClusters;

	if (tid < total) {
		int coord = tid / numClusters;
		int cluster = tid % numClusters;
		int count = devicenewClusterSize[cluster];

		if (count > 0) {
			deviceClusters[coord * numClusters + cluster] =
				devicenewClusters[coord * numClusters + cluster] / count;
		}
	}
}

//
//  ----------------------------------------
//  DATA LAYOUT
//
//  objects         [numObjs][numCoords]
//  clusters        [numClusters][numCoords]
//  dimObjects      [numCoords][numObjs]
//  dimClusters     [numCoords][numClusters]
//  newClusters     [numCoords][numClusters]
//  deviceObjects   [numCoords][numObjs]
//  deviceClusters  [numCoords][numClusters]
//  ----------------------------------------
//
/* return an array of cluster centers of size [numClusters][numCoords]       */
void kmeans_gpu(double *objects,      /* in: [numObjs][numCoords] */
		int numCoords,    /* no. features */
		int numObjs,      /* no. objects */
		int numClusters,  /* no. clusters */
		double threshold,    /* % objects change membership */
		long loop_threshold,   /* maximum number of iterations */
		int *membership,   /* out: [numObjs] */
		double *clusters,   /* out: [numClusters][numCoords] */
		int blockSize) {
	double timing = wtime(), timing_internal, timer_min = 1e42, timer_max = 0;
	double timing_gpu, timing_cpu, timing_transfers, transfers_time = 0.0, cpu_time = 0.0, gpu_time = 0.0;
	int i, j, loop = 0;
	double delta = 0, *dev_delta_ptr;          /* % of objects change their clusters */
	double **dimObjects = (double **) calloc_2d(numCoords, numObjs, sizeof(double));
	double **dimClusters = (double **) calloc_2d(numCoords, numClusters, sizeof(double));

	printf("\n|-----------Full-offload All Reduction GPU Kmeans------------|\n\n");

	for (i = 0; i < numObjs; i++) {
		for (j = 0; j < numCoords; j++) {
			dimObjects[j][i] = objects[i * numCoords + j];
		}
	}

	double *deviceObjects;
	double *deviceClusters;
	double *devicenewClustersBlocks, *devicenewClusters;
	int *deviceMembership;
	int *devicenewClusterSizeBlocks, *devicenewClusterSize; /* [numClusters]: no. objects assigned in each new cluster */
	double *devdeltaBlocks;

	/* pick first numClusters elements of objects[] as initial cluster centers*/
	for (i = 0; i < numCoords; i++) {
		for (j = 0; j < numClusters; j++) {
			dimClusters[i][j] = dimObjects[i][j];
		}
	}

	/* initialize membership[] */
	for (i = 0; i < numObjs; i++) membership[i] = -1;

	timing = wtime() - timing;
	printf("t_alloc: %lf ms\n\n", 1000 * timing);
	timing = wtime();
	const unsigned int numThreadsPerClusterBlock = (numObjs > blockSize) ? blockSize : numObjs;
	const unsigned int numClusterBlocks = (numObjs + numThreadsPerClusterBlock - 1) / numThreadsPerClusterBlock;

	/*	Define the shared memory needed per block.
		- BEWARE: Also add extra shmem for delta buffer.
		- BEWARE: We can overrun our shared memory here if there are too many
		clusters or too many coordinates!
		- This can lead to occupancy problems or even inability to run.
		- Your exercise implementation is not requested to account for that (e.g. always assume deviceClusters fit in shmemClusters */
	const unsigned int clusterBlockSharedDataSize =
		numClusters * numCoords * sizeof(double) +
		numThreadsPerClusterBlock * sizeof(double) +
		numClusters * sizeof(int);

	cudaDeviceProp deviceProp;
	int deviceNum;
	cudaGetDevice(&deviceNum);
	cudaGetDeviceProperties(&deviceProp, deviceNum);

	if (clusterBlockSharedDataSize > deviceProp.sharedMemPerBlock) {
		error("Your CUDA hardware has insufficient block shared memory to hold all cluster centroids\n");
	}

	checkCuda(cudaMalloc(&deviceObjects, numObjs * numCoords * sizeof(double)));
	checkCuda(cudaMalloc(&deviceClusters, numClusters * numCoords * sizeof(double)));
	checkCuda(cudaMalloc(&devicenewClustersBlocks,
				numClusterBlocks * numClusters * numCoords * sizeof(double)));
	checkCuda(cudaMalloc(&devicenewClusterSizeBlocks,
				numClusterBlocks * numClusters * sizeof(int)));
	checkCuda(cudaMalloc(&devicenewClusters, numClusters * numCoords * sizeof(double)));
	checkCuda(cudaMalloc(&devicenewClusterSize, numClusters * sizeof(int)));
	checkCuda(cudaMalloc(&deviceMembership, numObjs * sizeof(int)));
	checkCuda(cudaMalloc(&devdeltaBlocks, numClusterBlocks * sizeof(double)));
	checkCuda(cudaMalloc(&dev_delta_ptr, sizeof(double)));

	timing = wtime() - timing;
	printf("t_alloc_gpu: %lf ms\n\n", 1000 * timing);
	timing = wtime();

	checkCuda(cudaMemcpy(deviceObjects, dimObjects[0],
				numObjs * numCoords * sizeof(double), cudaMemcpyHostToDevice));
	checkCuda(cudaMemcpy(deviceMembership, membership,
				numObjs * sizeof(int), cudaMemcpyHostToDevice));
	checkCuda(cudaMemcpy(deviceClusters, dimClusters[0],
				numClusters * numCoords * sizeof(double), cudaMemcpyHostToDevice));
	checkCuda(cudaMemset(devicenewClusterSize, 0, numClusters * sizeof(int)));
	checkCuda(cudaMemset(devicenewClusters, 0, numClusters * numCoords * sizeof(double)));
	free(dimObjects[0]);
	free(dimObjects);
	timing = wtime() - timing;
	printf("t_get_gpu: %lf ms\n\n", 1000 * timing);
	timing = wtime();

	do {
		timing_internal = wtime();
		timing_gpu = wtime();

		//printf("Launching find_nearest_cluster Kernel with grid_size = %d, block_size = %d, shared_mem = %d KB\n", numClusterBlocks, numThreadsPerClusterBlock, clusterBlockSharedDataSize/1000);
		find_nearest_cluster
			<<< numClusterBlocks, numThreadsPerClusterBlock, clusterBlockSharedDataSize >>>
			(numCoords, numObjs, numClusters,
			 deviceObjects, deviceClusters,
			 devicenewClustersBlocks, devicenewClusterSizeBlocks,
			 deviceMembership, devdeltaBlocks);
		cudaDeviceSynchronize();
		checkLastCudaError();

		gpu_time += wtime() - timing_gpu;

		//printf("Kernels complete for itter %d, updating data in CPU\n", loop);

		const unsigned int reduce_clusters_block_sz =
			(numCoords * numClusters > blockSize) ? blockSize : numCoords * numClusters;
		const unsigned int reduce_clusters_dim_sz =
			(numCoords * numClusters + reduce_clusters_block_sz - 1) / reduce_clusters_block_sz;
		const unsigned int reduce_sizes_block_sz =
			(numClusters > blockSize) ? blockSize : numClusters;
		const unsigned int reduce_sizes_dim_sz =
			(numClusters + reduce_sizes_block_sz - 1) / reduce_sizes_block_sz;
		const unsigned int reduce_delta_block_sz =
			(numClusterBlocks > blockSize) ? blockSize : numClusterBlocks;

		timing_gpu = wtime();
		/* No atomics: explicit reduction across per-block outputs. */
		reduce_blocks<double>
			<<< reduce_clusters_dim_sz, reduce_clusters_block_sz >>>
			(devicenewClustersBlocks, devicenewClusters,
			 numClusterBlocks, numClusters * numCoords);
		reduce_blocks<int>
			<<< reduce_sizes_dim_sz, reduce_sizes_block_sz >>>
			(devicenewClusterSizeBlocks, devicenewClusterSize,
			 numClusterBlocks, numClusters);
		reduce_blocks<double>
			<<< 1, reduce_delta_block_sz >>>
			(devdeltaBlocks, dev_delta_ptr, numClusterBlocks, 1);
		cudaDeviceSynchronize();
		checkLastCudaError();
		gpu_time += wtime() - timing_gpu;

		timing_transfers = wtime();
		checkCuda(cudaMemcpy(&delta, dev_delta_ptr, sizeof(double), cudaMemcpyDeviceToHost));
		transfers_time += wtime() - timing_transfers;

		const unsigned int update_centroids_block_sz = (numCoords * numClusters > blockSize) ? blockSize : numCoords *
			numClusters;

		const unsigned int update_centroids_dim_sz =
			(numCoords * numClusters + update_centroids_block_sz - 1) / update_centroids_block_sz;
		timing_gpu = wtime();
		update_centroids<<< update_centroids_dim_sz, update_centroids_block_sz, 0 >>>
			(numCoords, numClusters, devicenewClusterSize, devicenewClusters, deviceClusters);
		cudaDeviceSynchronize();
		checkLastCudaError();
		gpu_time += wtime() - timing_gpu;

		timing_cpu = wtime();
		delta /= numObjs;
		//printf("delta is %f - ", delta);
		loop++;
		//printf("completed loop %d\n", loop);
		cpu_time += wtime() - timing_cpu;

		timing_internal = wtime() - timing_internal;
		if (timing_internal < timer_min) timer_min = timing_internal;
		if (timing_internal > timer_max) timer_max = timing_internal;
	} while (delta > threshold && loop < loop_threshold);


	checkCuda(cudaMemcpy(membership, deviceMembership,
				numObjs * sizeof(int), cudaMemcpyDeviceToHost));
	checkCuda(cudaMemcpy(dimClusters[0], deviceClusters,
				numClusters * numCoords * sizeof(double), cudaMemcpyDeviceToHost));

	for (i = 0; i < numClusters; i++) {
		//if (newClusterSize[i] > 0) {
		for (j = 0; j < numCoords; j++) {
			clusters[i * numCoords + j] = dimClusters[j][i];
		}
		//}
	}

	timing = wtime() - timing;
	printf("nloops = %d  : total = %lf ms\n\t-> t_loop_avg = %lf ms\n\t-> t_loop_min = %lf ms\n\t-> t_loop_max = %lf ms\n\t"
			"-> t_cpu_avg = %lf ms\n\t-> t_gpu_avg = %lf ms\n\t-> t_transfers_avg = %lf ms\n\n|-------------------------------------------|\n",
			loop, 1000 * timing, 1000 * timing / loop, 1000 * timer_min, 1000 * timer_max,
			1000 * cpu_time / loop, 1000 * gpu_time / loop, 1000 * transfers_time / loop);

	char outfile_name[1024] = {0};
	sprintf(outfile_name, "Execution_logs/silver1-V100_Sz-%lu_Coo-%d_Cl-%d.csv",
			numObjs * numCoords * sizeof(double) / (1024 * 1024), numCoords, numClusters);
	FILE *fp = fopen(outfile_name, "a+");
	if (!fp) error("Filename %s did not open succesfully, no logging performed\n", outfile_name);
	fprintf(fp, "%s,%d,%lf,%lf,%lf\n", "All_GPU_All_Reduction", blockSize, timing / loop, timer_min, timer_max);
	fclose(fp);

	checkCuda(cudaFree(deviceObjects));
	checkCuda(cudaFree(deviceClusters));
	checkCuda(cudaFree(devicenewClustersBlocks));
	checkCuda(cudaFree(devicenewClusterSizeBlocks));
	checkCuda(cudaFree(devdeltaBlocks));
	checkCuda(cudaFree(devicenewClusters));
	checkCuda(cudaFree(devicenewClusterSize));
	checkCuda(cudaFree(deviceMembership));
	checkCuda(cudaFree(dev_delta_ptr));

	free(dimClusters[0]);
	free(dimClusters);

	return;
}
