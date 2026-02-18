# Floyd-Warshall All-Pairs Shortest Path

Three implementations of the Floyd-Warshall algorithm for computing all-pairs shortest paths on a randomly generated graph.

## Source Files

| File | Description |
|------|-------------|
| `fw.c` | Standard O(n^3) sequential Floyd-Warshall with triple nested loops |
| `fw_sr.c` | Scale-and-recurse — recursive decomposition that halves the problem size at each level, parallelized with OpenMP for independent subproblems |
| `util.c/h` | Graph initialization (random weights) and timing utilities |

## Compiling

```bash
qsub -q serial -l nodes=sandman:ppn=64 make_on_queue.sh
```

Produces three executables: `fw`, `fw_sr`.

## Running

Run experiments through the queue:

```bash
qsub -q serial -l nodes=sandman:ppn=64 script.sh
```

Replace `script.sh` with your run queue script. This directory already provides `make_on_queue.sh` for compilation.

- `N` — graph size (number of vertices)
- `B` — tile/block size (for tiled version only)
- `output_file` — file to write distance results

Experiment parameters are configured in the queue script.

## Future Work
- Implement a tiled version of Floyd-Warshall for better cache performance.
- Explore MPI-based distributed-memory implementations for larger graphs.
