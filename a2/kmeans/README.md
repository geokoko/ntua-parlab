# K-Means Clustering (OpenMP)

Parallel k-means clustering comparing three parallelization strategies: sequential baseline, naive OpenMP with critical sections, and reduction-based OpenMP. Includes analysis of false-sharing effects on performance.

## Source Files

| File | Description |
|------|-------------|
| `main.c` | Unified driver — parses arguments, generates dataset, invokes the selected k-means variant, reports timing |
| `seq_kmeans.c` | Sequential baseline — standard iterative k-means with Euclidean distance |
| `omp_naive_kmeans.c` | Naive OpenMP — parallel assignment phase with critical sections for centroid updates |
| `omp_reduction_kmeans.c` | Reduction-based OpenMP — uses OpenMP reduction clauses for centroid accumulation, avoids critical sections |
| `file_io.c` | Dataset I/O (read/write) |
| `util.c` | Utility functions (timing, random number generation) |
| `kmeans.h` | Shared data structures and function declarations |

## Compiling

```bash
qsub -q serial -l nodes=sandman:ppn=64 make_on_queue.sh
```

Produces: `kmeans_seq`, `kmeans_omp_naive`, `kmeans_omp_reduction`.

## Running

```bash
qsub -q serial -l nodes=sandman:ppn=64 run_on_queue.sh
```

| Flag | Description | Default |
|------|-------------|---------|
| `-c` | Number of clusters (must be > 1) | — |
| `-s` | Dataset size | — |
| `-n` | Number of coordinates per point | — |
| `-t` | Convergence threshold | 0.001 |
| `-l` | Maximum iterations | 10 |
| `-d` | Enable debug mode | off |

Example:

```bash
qsub -q serial -l nodes=sandman:ppn=64 run_on_queue.sh
```
