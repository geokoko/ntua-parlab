# Parallel Processing Systems - ECE NTUA

Course assignments for Parallel Processing Systems at the National Technical University of Athens (9th semester). Four assignments covering the full spectrum of parallel programming: shared-memory (OpenMP, Pthreads), GPU (CUDA), and distributed-memory (MPI).

## Students Involved
- [Georgios Kokoromytis](https://github.com/geokoko)
- [Odysseas-Arthouros-Rigas Tsouknidas](https://github.com/odysseastsouknidas)
- [Konstantinos Fezos](https://github.com/feezz8)

## Repository Structure

```
a1/   - OpenMP Game of Life
a2/   - Shared-memory parallel algorithms (OpenMP, Pthreads)
a3/   - CUDA GPU k-means implementations
a4/   - MPI distributed heat transfer & k-means
```

## Assignments

### [Assignment 1 — Game of Life (OpenMP)](a1/README.md)

Conway's Game of Life on an N x N grid, parallelized with OpenMP. Supports configurable grid size, timesteps, and optional GIF output.

### [Assignment 2 — Shared-Memory Parallel Algorithms](a2/README.md)

Four sub-projects exploring different parallelization and synchronization strategies:

- **[Concurrent Linked List](a2/conc_ll/README.md)** — Six linked list implementations benchmarking different synchronization: serial, coarse-grain lock, fine-grain lock, optimistic, lazy deletion, and lock-free (CAS)
- **[Floyd-Warshall](a2/FW/README.md)** — All-pairs shortest path: standard, tiled (cache-optimized), and scale-and-recurse (recursive blocking), parallelized with OpenMP
- **[K-Means Clustering](a2/kmeans/README.md)** — Sequential, naive OpenMP, and reduction-based OpenMP with false-sharing analysis
- **[K-Means with Lock Variants](a2/kmeans_locks/README.md)** — Nine synchronization strategies: OpenMP critical, TAS, TTAS, CLH, array lock, pthread mutex/spinlock

### [Assignment 3 — CUDA K-Means](a3/README.md)

GPU-accelerated k-means with eight CUDA kernel variants exploring shared memory, coalesced access, fused kernels, and parallel reduction optimizations.

**Requirements:** CUDA toolkit, NVIDIA Tesla V100 or similar GPU.

### [Assignment 4 — MPI Distributed Computing](a4/README.md)

- **[MPI K-Means](a4/kmeans/README.md)** — Distributed k-means using MPI data partitioning and collective centroid updates
- **[Heat Transfer](a4/heat_transfer/README.md)** — 2D heat equation with three solvers (Jacobi, Gauss-Seidel SOR, Red-Black SOR), each with serial and MPI versions using 2D Cartesian domain decomposition and ghost cell exchanges

## Technologies used

- The core implementations have been done using **C** as the programming language.
- For implementing **shared-memory address space parallelism** (a1, a2, a4), **OpenMP** was used.
- For **GPU parallelism**, we utilized the **CUDA** framework (a3).
- For **Distributed-memory parallelism** (a4), we used **MPI** (Message Passing Interface).
- Python's matplotlib library was used for plotting and performance analysis.

## Building

Each assignment directory contains its own `Makefile`. See the individual READMEs linked above for specific compilation and usage instructions.

## Queue Usage Summary

Experiments are submitted via PBS queue scripts:

- **A4 (MPI):** `qsub -q parlab -l nodes=...:ppn=... script.sh`
- **A3 (CUDA):** `qsub -q serial -l nodes=silver1:ppn=40 script.sh`
- **A1/A2 (OpenMP):** `qsub -q serial -l nodes=sandman:ppn=64 script.sh`

Replace `script.sh` with the appropriate `make_on_queue.sh` or `run_on_queue.sh` script for each subdirectory.

## Utilities

`scirouter/` contains scripts (`push.sh`, `pull.sh`) for transferring data to/from CSLab's `scirouter` server. To use these scripts, follow the instructions [here](scirouter/README.md).
