# Assignment 4 - MPI Distributed Computing

Distributed-memory implementations using MPI: k-means clustering with data partitioning and 2D heat equation solvers with domain decomposition.

## Queue-Based Compilation & Execution

All A4 experiments are compiled and run through the cluster queue.

```bash
qsub -q parlab -l nodes=...:ppn=... make_on_queue.sh
qsub -q parlab -l nodes=...:ppn=... run_on_queue.sh
```

Replace `nodes`/`ppn` according to your experiment and use the `make_on_queue.sh` / `run_on_queue.sh` scripts available inside each MPI subdirectory.

## Sub-projects

### [MPI K-Means](kmeans/)

Distributed k-means clustering using MPI. Data is partitioned across processes, each computing local assignments. Global centroid updates are performed via MPI collective operations.

### [Heat Transfer](heat_transfer/)

2D heat equation solved with three iterative methods (Jacobi, Gauss-Seidel SOR, Red-Black SOR), each with serial and MPI versions. MPI versions use 2D Cartesian topology with halo (ghost cell) exchanges.
