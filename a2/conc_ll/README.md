# Concurrent Linked List

Benchmarks six sorted linked list implementations under concurrent access. Each variant uses a different synchronization strategy. Threads perform a mix of `contains`, `add`, and `remove` operations for 10 seconds and throughput (total operations) is measured.

## Source Files

| File | Description |
|------|-------------|
| `main.c` | Benchmark driver: spawns threads, sets CPU affinity, measures throughput with padding to avoid false sharing |
| `ll/ll_serial.c` | Serial baseline — no synchronization, sentinel nodes at head/tail |
| `ll/ll_cgl.c` | Coarse-grained locking — single `pthread_spinlock_t` protects entire list |
| `ll/ll_fgl.c` | Fine-grained locking — per-node spinlock, hand-over-hand traversal |
| `ll/ll_opt.c` | Optimistic locking — lock-free traversal, then lock and validate |
| `ll/ll_lazy.c` | Lazy deletion — logical delete via marked nodes, optimistic traversal |
| `ll/ll_nb.c` | Non-blocking (lock-free) — CAS-based (`__sync_val_compare_and_swap`) |
| `lib/aff.c` | CPU affinity utilities for thread pinning |
| `lib/timer.h` | Timing macros |

## Compiling

```bash
qsub -q serial -l nodes=sandman:ppn=64 make_on_queue.sh
```

Produces six executables: `x.serial`, `x.cgl`, `x.fgl`, `x.opt`, `x.lazy`, `x.nb`.

## Running

Run experiments via the queue:

```bash
qsub -q serial -l nodes=sandman:ppn=64 script.sh
```

Replace `script.sh` with your run queue script. This directory already provides `make_on_queue.sh` for compilation.

- `list_size` — initial number of elements in the list
- `contains_pct` — percentage of contains operations (0-100)
- `add_pct` — percentage of add operations (0-100)
- `remove_pct` — percentage of remove operations (0-100)
- The three percentages must sum to 100

The benchmark configuration is controlled inside the run queue script.
