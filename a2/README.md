# Assignment 2 - Shared-Memory Parallel Algorithms

Four sub-projects exploring different parallelization and synchronization strategies using OpenMP and Pthreads.

## Queue-Based Compilation & Execution

All A2 experiments are run through the queue:

```bash
qsub -q serial -l nodes=sandman:ppn=64 script.sh
```

Replace `script.sh` with `make_on_queue.sh` or `run_on_queue.sh` depending on the subproject.

## Sub-projects

### [Concurrent Linked List](conc_ll/)

Benchmarks six linked list implementations with different synchronization primitives (serial, coarse-grain lock, fine-grain lock, optimistic, lazy deletion, lock-free). Measures throughput under concurrent access with configurable operation mix.

### [Floyd-Warshall](FW/)

All-pairs shortest path with three implementations: standard O(n^3), cache-optimized tiled (OpenMP) (**pending implementation**), and recursive scale-and-recurse (OpenMP).

### [K-Means Clustering](kmeans/)

Parallel k-means comparing sequential, naive OpenMP (critical sections), and reduction-based OpenMP approaches, with analysis of false-sharing effects.

### [K-Means with Lock Variants](kmeans_locks/)

K-means clustering using nine different synchronization strategies: naive OpenMP, critical sections, and seven lock implementations (no-sync, pthread mutex, pthread spinlock, TAS, TTAS, array lock, CLH queue lock).
