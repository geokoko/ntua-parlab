# Heat Transfer - 2D Heat Equation

Solves the 2D heat equation using three iterative methods, each with serial and MPI implementations. MPI versions use 2D Cartesian domain decomposition with ghost cell (halo) exchanges via `MPI_Sendrecv`.

## Methods

### [Jacobi](jacobi/)

Explicit synchronous updates: each cell is updated from its four neighbors in the previous iteration. Both arrays are swapped between iterations.

```
u_current[i][j] = (u_prev[i-1][j] + u_prev[i+1][j] + u_prev[i][j-1] + u_prev[i][j+1]) / 4.0
```

### [Gauss-Seidel SOR](gauss_seidel/)

Successive Over-Relaxation — uses newly computed values from the current iteration as they become available, accelerated with a relaxation parameter omega.

### [Red-Black SOR](red_black/)

Checkerboard ordering — cells are colored red/black in a checkerboard pattern. All red cells are updated first, then all black cells, enabling better parallelism since same-color cells are independent.

## Directory Structure

Each method has `serial/` and `mpi/` subdirectories, each with its own Makefile.

```
heat_transfer/
├── jacobi/
│   ├── serial/        # Jacobi_serial.c
│   └── mpi/           # jacobi_mpi.c
├── gauss_seidel/
│   ├── serial/        # GaussSeidelSOR_serial.c
│   └── mpi/           # gauss_seidel_mpi.c
└── red_black/
    ├── serial/        # RedBlackSOR_serial.c
    └── mpi/           # red_black_mpi.c
```

## Compiling

Compilation is submitted through the queue from each method/version subdirectory:

```bash
qsub -q parlab -l nodes=...:ppn=... make_on_queue.sh
```

This builds the method-specific executables (constant-iteration and convergence variants) defined by each subdirectory `Makefile`.

## Running

Execution is also submitted through the queue:

```bash
qsub -q parlab -l nodes=...:ppn=... run_on_queue.sh
```

Replace `nodes`/`ppn` according to your experiment. The MPI implementations automatically create a 2D Cartesian process topology via `MPI_Dims_create` and `MPI_Cart_create`, decomposing the domain across all processes. Ghost cell exchanges happen at each iteration via `MPI_Sendrecv`.

The `_converge` variants (compiled with `-DTEST_CONV`) terminate when the global residual falls below a threshold, detected via `MPI_Allreduce`.
