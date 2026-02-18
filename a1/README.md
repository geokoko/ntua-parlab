# Assignment 1 - Game of Life (OpenMP)

Conway's Game of Life on an N x N grid, parallelized with OpenMP. The simulation applies standard Game of Life rules (birth, survival, death) at each timestep using a double-buffered grid that swaps between current and previous states.

## Source Files

| File | Description |
|------|-------------|
| `Game_Of_Life.c` | Full implementation: grid allocation, random initialization, parallel simulation loop, optional PGM image output |

The innermost loop is parallelized with `#pragma omp parallel for`, distributing row computation across threads. Timing is measured with `gettimeofday()`.

## Compiling

```bash
qsub -q serial -l nodes=sandman:ppn=64 make_on_queue.sh
```

Compiles with `gcc -O3 -fopenmp`. To enable GIF output (requires ImageMagick):

```bash
gcc -O3 -fopenmp -DOUTPUT -o game_of_life Game_Of_Life.c
```

## Running

```bash
qsub -q serial -l nodes=sandman:ppn=64 run_on_queue.sh
```

Replace `script.sh` with either `make_on_queue.sh` or `run_on_queue.sh` depending on whether you are compiling or running.

- `grid_size` — side length of the square grid
- `timesteps` — number of simulation iterations

When compiled with `-DOUTPUT`, PGM frames are written and converted to `output.gif` via ImageMagick. Avoid this for large grids or many timesteps.
