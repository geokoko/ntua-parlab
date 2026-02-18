# K-Means with Lock Variants

K-means clustering implemented with nine different synchronization strategies to study the performance impact of various locking primitives.

## Source Files

| File | Description |
|------|-------------|
| `main.c` | Unified driver — argument parsing, dataset generation, timing |
| `omp_naive_kmeans.c` | Naive OpenMP — no explicit synchronization for centroid updates |
| `omp_critical_kmeans.c` | Uses `#pragma omp critical` for centroid updates |
| `omp_lock_kmeans.c` | Generic lock-based k-means — links against different lock implementations |
| `locks/nosync_lock.c` | No-op lock (no synchronization, baseline) |
| `locks/pthread_mutex_lock.c` | POSIX mutex lock |
| `locks/pthread_spin_lock.c` | POSIX spinlock |
| `locks/tas_lock.c` | Test-and-Set lock (atomic) |
| `locks/ttas_lock.c` | Test-Test-and-Set lock |
| `locks/array_lock.c` | Array-based lock |
| `locks/clh_lock.c` | CLH queue lock |
| `file_io.c` | Dataset I/O |
| `util.c` | Utilities (timing, RNG) |

## Compiling

```bash
qsub -q serial -l nodes=sandman:ppn=64 make_on_queue.sh
```

Produces nine executables:

- `kmeans_omp_naive`
- `kmeans_omp_critical`
- `kmeans_omp_nosync_lock`
- `kmeans_omp_pthread_mutex_lock`
- `kmeans_omp_pthread_spin_lock`
- `kmeans_omp_tas_lock`
- `kmeans_omp_ttas_lock`
- `kmeans_omp_array_lock`
- `kmeans_omp_clh_lock`

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
