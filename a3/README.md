# Assignment 3 - CUDA K-Means

GPU-accelerated k-means clustering with eight CUDA kernel variants, each targeting a different GPU optimization strategy.

## Kernel Implementations

| File | Optimization |
|------|-------------|
| `cuda_kmeans_naive.cu` | Baseline GPU implementation — each thread computes nearest cluster for one point |
| `cuda_kmeans_shared.cu` | Cluster centroids loaded into shared memory to reduce global memory accesses |
| `cuda_kmeans_transpose.cu` | Transposed data layout for coalesced memory access patterns |
| `cuda_kmeans_all_gpu.cu` | Centroid recomputation moved entirely to GPU (avoids host round-trip) |
| `cuda_kmeans_all_gpu_single_kernel.cu` | Fused assignment + centroid update in a single kernel launch (Not used in report due to unexpected slowdowns) |
| `cuda_kmeans_all_gpu_reduction.cu` | GPU-based parallel reduction for centroid accumulation |
| `cuda_kmeans_all_gpu_delta_reduction.cu` | Convergence delta computed on GPU via parallel reduction |
| `cuda_kmeans_all_gpu_all_reduction.cu` | Full pipeline on GPU — assignment, centroid update, and convergence check all use parallel reduction |

## Other Source Files

| File | Description |
|------|-------------|
| `main_gpu.cu` | GPU driver — argument parsing, kernel selection, memory management, optional validation against sequential |
| `main_sec.c` | Sequential driver for reference/validation |
| `seq_kmeans.c` | Sequential k-means implementation |
| `helper_functions/alloc.c` | GPU memory allocation/deallocation helpers |
| `helper_functions/error.c` | CUDA error checking (`checkCuda()`) |
| `helper_functions/file_io.c` | Dataset I/O |
| `helper_functions/util.c` | Utilities (timing, distance calculations) |
| `helper_functions/kmeans.h` | Shared declarations and data structures |
| `plot_results.py` | Performance visualization script |

## Requirements

- CUDA Toolkit
- GPU NVIDIA Tesla V100 or similar

## Compiling

By default, only `kmeans_seq` and `kmeans_cuda_naive` are built. To enable other variants, uncomment the desired targets in the `Makefile` `all:` line.

```bash
qsub -q serial -l nodes=silver1:ppn=40 make_on_queue.sh
```

To enable validation against the sequential implementation, uncomment `VALIDATE_FLAG=-DVALIDATE` in the Makefile.

## Compiling & Running

```bash
qsub -q serial -l nodes=silver1:ppn=40 run_on_queue.sh
```

Use `make_on_queue.sh` for compilation and `run_on_queue.sh` for experiments.

| Flag | Description | Default |
|------|-------------|---------|
| `-c` | Number of clusters (must be > 1) | — |
| `-s` | Dataset size | — |
| `-n` | Number of coordinates per point | — |
| `-t` | Convergence threshold | 0.001 |
| `-l` | Maximum iterations | 10 |
| `-b` | CUDA block size (threads per block) | — |
| `-d` | Enable debug mode | off |

Example:

```bash
qsub -q serial -l nodes=silver1:ppn=40 run_on_queue.sh
```
