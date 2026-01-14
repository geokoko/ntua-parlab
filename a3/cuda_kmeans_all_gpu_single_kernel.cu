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
	// DONE 
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

	/* DONE: Calculate the euclid_dist of elem=objectId of objects from elem=clusterId from clusters, but for column-base format!!! */
	for (i = 0; i < numCoords; i++) {
		double diff = objects[i * numObjs + objectId] - clusters[i * numClusters + clusterId];
		ans += diff * diff;
	}

	return (ans);
}

__device__ __forceinline__
void grid_sync(unsigned int *block_counter, unsigned int *block_flag) {
	__shared__ int is_last_block;

	__syncthreads();
	if (threadIdx.x == 0) {
		__threadfence();
		unsigned int ticket = atomicAdd(block_counter, 1);
		is_last_block = (ticket == gridDim.x - 1);
	}
	__syncthreads();

	if (is_last_block) {
		*block_flag = 1;
		__threadfence();
	} else {
		volatile unsigned int *flag_ptr = block_flag;
		while (*flag_ptr == 0) { }
	}
	__syncthreads();
}

// --- ---
/* Runs in parallel on the GPU to find the nearest cluster for each object.
 * Single-kernel variant: also update new centroid accumulators here. */
__global__ static
void find_nearest_cluster(int numCoords,
		int numObjs,
		int numClusters,
		double *objects,           		//  [numCoords][numObjs]
		int *devicenewClusterSize,		//  [numClusters]
		double *devicenewClusters,		//  [numCoords][numClusters]
		double *deviceClusters,    		//  [numCoords][numClusters]
		int *deviceMembership,          //  [numObjs]
		double *devdelta,
		unsigned int *block_counter,
		unsigned int *block_flag) {
	extern __shared__ double shmemClusters[];

	/* DONE: Copy deviceClusters to shmemClusters so they can be accessed faster.
	BEWARE: Make sure operations is complete before any thread continues... */
	int i;
	for (i = threadIdx.x; i < numClusters * numCoords; i += blockDim.x) {
		shmemClusters[i] = deviceClusters[i];
	}
	/* Use this so all threads wait until copy is done */
	__syncthreads();

	/* Get the global ID of the thread. */
	int tid = get_tid();

	/* DONE: Run only threads that are tied to a kmeans object */
	if (tid < numObjs) {
		int index, i;
		double dist, min_dist;

		/* find the cluster id that has min distance to object */
		index = 0;
		/* DONE: call min_dist = euclid_dist_2(...) with correct objectId/clusterId using clusters in shmem*/
		/* Let cluster 0 be the initial minimum distance */
		min_dist = euclid_dist_2_transpose(numCoords, numObjs, numClusters, objects, shmemClusters, tid, 0);

		/* iterate over all clusters to find the nearest */
		for (i = 1; i < numClusters; i++) {
			/* DONE: call dist = euclid_dist_2(...) with correct objectId/clusterId using clusters in shmem*/
			dist = euclid_dist_2_transpose(numCoords, numObjs, numClusters, objects, shmemClusters, tid, i);
			/* no need square root */
			if (dist < min_dist) { /* find the min and its array index */
				min_dist = dist;
				index = i;
			}
		}

		if (deviceMembership[tid] != index) {
			/* DONE: atomic add to devdelta */
			atomicAdd(devdelta, 1.0);
		}

		/* assign the deviceMembership to object objectId */
		deviceMembership[tid] = index;

		atomicAdd(&devicenewClusterSize[index], 1);
		for (i = 0; i < numCoords; i++) {
			atomicAdd(&devicenewClusters[i * numClusters + index], objects[i * numObjs + tid]);
		}
	}

	/* Synchronize all blocks to move to the next step (centroid calculation) */
	grid_sync(block_counter, block_flag);

	/* NOW UPDATE THE CENTROIDS */
	int gid = get_tid();
	int total = numCoords * numClusters;

	if (gid < total) {
		int coord = gid / numClusters;
		int cluster = gid % numClusters;
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
	/* Transpose dims */
	double **dimObjects = (double **) calloc_2d(numCoords, numObjs, sizeof(double)); // [numCoords][numObjs]
	double **dimClusters = (double **) calloc_2d(numCoords, numClusters, sizeof(double));  // [numCoords][numClusters]

	printf("\n|------Full-offload Single-kernel GPU Kmeans------|\n\n");

	/* Copy objects to [numCoords][numObjs] layout */
	for (i = 0; i < numObjs; i++) {
		for (j = 0; j < numCoords; j++) {
			dimObjects[j][i] = objects[i * numCoords + j];
		}
	}

	double *deviceObjects;
	double *deviceClusters, *devicenewClusters;
	int *deviceMembership;
	int *devicenewClusterSize; /* [numClusters]: no. objects assigned in each new cluster */
	unsigned int *deviceBlockCounter;
	unsigned int *deviceBlockFlag;

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
		- BEWARE: We can overrun our shared memory here if there are too many
		clusters or too many coordinates!
		- This can lead to occupancy problems or even inability to run.
		- Your exercise implementation is not requested to account for that (e.g. always assume deviceClusters fit in shmemClusters */
	const unsigned int clusterBlockSharedDataSize = numClusters * numCoords * sizeof(double);
	
	/* Check if the device has enough shared memory */
	cudaDeviceProp deviceProp;
	int deviceNum;
	cudaGetDevice(&deviceNum);
	cudaGetDeviceProperties(&deviceProp, deviceNum);

	if (clusterBlockSharedDataSize > deviceProp.sharedMemPerBlock) {
		error("Your CUDA hardware has insufficient block shared memory to hold all cluster centroids\n");
	}

	checkCuda(cudaMalloc(&deviceObjects, numObjs * numCoords * sizeof(double)));
	checkCuda(cudaMalloc(&deviceClusters, numClusters * numCoords * sizeof(double)));
	checkCuda(cudaMalloc(&devicenewClusters, numClusters * numCoords * sizeof(double)));
	checkCuda(cudaMalloc(&devicenewClusterSize, numClusters * sizeof(int)));
	checkCuda(cudaMalloc(&deviceMembership, numObjs * sizeof(int)));
	checkCuda(cudaMalloc(&dev_delta_ptr, sizeof(double)));
	checkCuda(cudaMalloc(&deviceBlockCounter, sizeof(unsigned int)));
	checkCuda(cudaMalloc(&deviceBlockFlag, sizeof(unsigned int)));

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
	checkCuda(cudaMemset(deviceBlockCounter, 0, sizeof(unsigned int)));
	checkCuda(cudaMemset(deviceBlockFlag, 0, sizeof(unsigned int)));
	free(dimObjects[0]);
	free(dimObjects);

	timing = wtime() - timing;
	printf("t_get_gpu: %lf ms\n\n", 1000 * timing);
	timing = wtime();

	do {
		timing_internal = wtime();
		checkCuda(cudaMemset(devicenewClusterSize, 0, numClusters * sizeof(int)));
		checkCuda(cudaMemset(devicenewClusters, 0, numClusters * numCoords * sizeof(double)));
		checkCuda(cudaMemset(dev_delta_ptr, 0, sizeof(double)));
		checkCuda(cudaMemset(deviceBlockCounter, 0, sizeof(unsigned int)));
		checkCuda(cudaMemset(deviceBlockFlag, 0, sizeof(unsigned int)));
		timing_gpu = wtime();
		find_nearest_cluster
			<<< numClusterBlocks, numThreadsPerClusterBlock, clusterBlockSharedDataSize >>>
			(numCoords, numObjs, numClusters,
			 deviceObjects, devicenewClusterSize, devicenewClusters,
			 deviceClusters, deviceMembership, dev_delta_ptr,
			 deviceBlockCounter, deviceBlockFlag);

		cudaDeviceSynchronize();
		checkLastCudaError();

		gpu_time += wtime() - timing_gpu;

		timing_transfers = wtime();
		checkCuda(cudaMemcpy(&delta, dev_delta_ptr, sizeof(double), cudaMemcpyDeviceToHost));
		transfers_time += wtime() - timing_transfers;

		/* No second kernel here; update centroids inside find_nearest_cluster. */

		timing_cpu = wtime();
		delta /= numObjs;
		loop++;
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
		for (j = 0; j < numCoords; j++) {
			clusters[i * numCoords + j] = dimClusters[j][i];
		}
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
	fprintf(fp, "%s,%d,%lf,%lf,%lf\n", "All_GPU_Single_Kernel", blockSize, timing / loop, timer_min, timer_max);
	fclose(fp);

	checkCuda(cudaFree(deviceObjects));
	checkCuda(cudaFree(deviceClusters));
	checkCuda(cudaFree(devicenewClusters));
	checkCuda(cudaFree(devicenewClusterSize));
	checkCuda(cudaFree(deviceMembership));
	checkCuda(cudaFree(dev_delta_ptr));
	checkCuda(cudaFree(deviceBlockCounter));
	checkCuda(cudaFree(deviceBlockFlag));

	free(dimClusters[0]);
	free(dimClusters);

	return;
}
