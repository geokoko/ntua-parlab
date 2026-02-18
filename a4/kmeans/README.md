# MPI K-Means Clustering

Distributed k-means clustering using MPI. The dataset is partitioned across MPI processes, each process computes nearest-cluster assignments for its local subset, and global centroid updates are performed via MPI collective operations (Allreduce).

## Source Files

| File | Description |
|------|-------------|
| `main.c` | MPI driver — initializes MPI, partitions data by rank (`rank_numObjs`), collects global membership via MPI operations |
| `kmeans.c` | Core k-means logic — distance calculations, centroid updates, membership tracking |
| `file_io.c` | Distributed dataset I/O |
| `util.c` | Utilities (timing) |
| `kmeans.h` | Shared declarations |

Also includes `sequential/` and `openmp-kmeans/` subdirectories with baseline implementations for comparison.

## Compiling

Compilation is performed through the queue:

```bash
qsub -q parlab -l nodes=...:ppn=... make_on_queue.sh
```

Produces: `kmeans_mpi`.

## Running

```bash
qsub -q parlab -l nodes=...:ppn=... run_on_queue.sh
```

Use `nodes`/`ppn` values appropriate for your experiment.

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
qsub -q parlab -l nodes=8:ppn=8 run_on_queue.sh
```
