#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/time.h>
#include "mpi.h"
#include "utils.h"

void RedSOR(double **u_previous, double **u_current, int X_min, int X_max, int Y_min, int Y_max,
            double omega) {
    int i, j;
    for (i = X_min; i < X_max; i++) {
        for (j = Y_min; j < Y_max; j++) {
            if ((i + j) % 2 == 0) {
                u_current[i][j] = u_previous[i][j]
                                 + (omega / 4.0)
                                       * (u_previous[i - 1][j] + u_previous[i + 1][j]
                                          + u_previous[i][j - 1] + u_previous[i][j + 1]
                                          - 4.0 * u_previous[i][j]);
            }
        }
    }
}

void BlackSOR(double **u_previous, double **u_current, int X_min, int X_max, int Y_min, int Y_max,
              double omega) {
    int i, j;
    for (i = X_min; i < X_max; i++) {
        for (j = Y_min; j < Y_max; j++) {
            if ((i + j) % 2 == 1) {
                u_current[i][j] = u_previous[i][j]
                                 + (omega / 4.0)
                                       * (u_current[i - 1][j] + u_current[i + 1][j]
                                          + u_current[i][j - 1] + u_current[i][j + 1]
                                          - 4.0 * u_previous[i][j]);
            }
        }
    }
}

int main(int argc, char **argv) {
    int rank, size;
    int global[2], local[2];
    int global_padded[2];
    int grid[2];
    int i, j, t;
    int global_converged = 0, converged = 0;
    MPI_Datatype dummy;
    MPI_Status status;
    double omega;

    struct timeval tts, ttf, tcs, tcf, tcvs, tcvf;
    double ttotal = 0, tcomp = 0, tconv = 0;
    double total_time, comp_time, conv_time, comm_time;

    double **U, **u_current, **u_previous, **swap;

    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);

    if (argc != 5) {
        fprintf(stderr, "Usage: mpirun .... ./exec X Y Px Py");
        exit(-1);
    } else {
        global[0] = atoi(argv[1]);
        global[1] = atoi(argv[2]);
        grid[0] = atoi(argv[3]);
        grid[1] = atoi(argv[4]);
    }

    MPI_Comm CART_COMM;
    int periods[2] = {0, 0};
    int rank_grid[2];

    MPI_Cart_create(MPI_COMM_WORLD, 2, grid, periods, 0, &CART_COMM);
    MPI_Cart_coords(CART_COMM, rank, 2, rank_grid);

    for (i = 0; i < 2; i++) {
        if (global[i] % grid[i] == 0) {
            local[i] = global[i] / grid[i];
            global_padded[i] = global[i];
        } else {
            local[i] = (global[i] / grid[i]) + 1;
            global_padded[i] = local[i] * grid[i];
        }
    }

    omega = 2.0 / (1 + sin(3.14 / global[0]));

    if (rank == 0) {
        U = allocate2d(global_padded[0], global_padded[1]);
        init2d(U, global[0], global[1]);
    }

    u_previous = allocate2d(local[0] + 2, local[1] + 2);
    u_current = allocate2d(local[0] + 2, local[1] + 2);

    MPI_Datatype global_block;
    MPI_Type_vector(local[0], local[1], global_padded[1], MPI_DOUBLE, &dummy);
    MPI_Type_create_resized(dummy, 0, sizeof(double), &global_block);
    MPI_Type_commit(&global_block);

    MPI_Datatype local_block;
    MPI_Type_vector(local[0], local[1], local[1] + 2, MPI_DOUBLE, &dummy);
    MPI_Type_create_resized(dummy, 0, sizeof(double), &local_block);
    MPI_Type_commit(&local_block);

    int *scatteroffset = NULL;
    int *scattercounts = NULL;
    if (rank == 0) {
        scatteroffset = (int *)malloc(size * sizeof(int));
        scattercounts = (int *)malloc(size * sizeof(int));
        for (i = 0; i < grid[0]; i++) {
            for (j = 0; j < grid[1]; j++) {
                scattercounts[i * grid[1] + j] = 1;
                scatteroffset[i * grid[1] + j] = (local[0] * local[1] * grid[1] * i + local[1] * j);
            }
        }
    }

    double *U0_ptr = NULL;
    if (rank == 0) {
        U0_ptr = &(U[0][0]);
    }

    MPI_Scatterv(U0_ptr, scattercounts, scatteroffset, global_block, &(u_previous[1][1]), 1, local_block, 0,
                 MPI_COMM_WORLD);
    MPI_Scatterv(U0_ptr, scattercounts, scatteroffset, global_block, &(u_current[1][1]), 1, local_block, 0,
                 MPI_COMM_WORLD);

    if (rank == 0) {
        free2d(U);
    }

    MPI_Datatype column;
    MPI_Type_vector(local[0], 1, local[1] + 2, MPI_DOUBLE, &dummy);
    MPI_Type_create_resized(dummy, 0, sizeof(double), &column);
    MPI_Type_commit(&column);

    int north, south, east, west;
    MPI_Cart_shift(CART_COMM, 0, 1, &north, &south);
    MPI_Cart_shift(CART_COMM, 1, 1, &west, &east);

    int i_min, i_max, j_min, j_max;

    i_min = 1;
    i_max = local[0] + 1;
    if (north == MPI_PROC_NULL) {
        i_min = 2;
    }
    if (south == MPI_PROC_NULL) {
        i_max -= (global_padded[0] - global[0]) + 1;
    }

    j_min = 1;
    j_max = local[1] + 1;
    if (west == MPI_PROC_NULL) {
        j_min = 2;
    }
    if (east == MPI_PROC_NULL) {
        j_max -= (global_padded[1] - global[1]) + 1;
    }

    MPI_Barrier(MPI_COMM_WORLD);
    gettimeofday(&tts, NULL);
#ifdef TEST_CONV
    for (t = 0; t < T && !global_converged; t++) {
#endif
#ifndef TEST_CONV
#undef T
#define T 256
    for (t = 0; t < T; t++) {
#endif
        swap = u_previous;
        u_previous = u_current;
        u_current = swap;

        if (north != MPI_PROC_NULL) {
            MPI_Sendrecv(&u_previous[1][1], local[1], MPI_DOUBLE, north, 0, &u_previous[0][1], local[1], MPI_DOUBLE,
                         north, 0, MPI_COMM_WORLD, &status);
        }
        if (south != MPI_PROC_NULL) {
            MPI_Sendrecv(&u_previous[local[0]][1], local[1], MPI_DOUBLE, south, 0, &u_previous[local[0] + 1][1],
                         local[1], MPI_DOUBLE, south, 0, MPI_COMM_WORLD, &status);
        }
        if (east != MPI_PROC_NULL) {
            MPI_Sendrecv(&u_previous[1][local[1]], 1, column, east, 0, &u_previous[1][local[1] + 1], 1, column, east,
                         0, MPI_COMM_WORLD, &status);
        }
        if (west != MPI_PROC_NULL) {
            MPI_Sendrecv(&u_previous[1][1], 1, column, west, 0, &u_previous[1][0], 1, column, west, 0,
                         MPI_COMM_WORLD, &status);
        }

        for (i = 0; i < local[0] + 2; i++) {
            u_current[i][0] = u_previous[i][0];
            u_current[i][local[1] + 1] = u_previous[i][local[1] + 1];
        }
        for (j = 0; j < local[1] + 2; j++) {
            u_current[0][j] = u_previous[0][j];
            u_current[local[0] + 1][j] = u_previous[local[0] + 1][j];
        }

        gettimeofday(&tcs, NULL);
        RedSOR(u_previous, u_current, i_min, i_max, j_min, j_max, omega);

        if (north != MPI_PROC_NULL) {
            MPI_Sendrecv(&u_current[1][1], local[1], MPI_DOUBLE, north, 1, &u_current[0][1], local[1], MPI_DOUBLE,
                         north, 1, MPI_COMM_WORLD, &status);
        }
        if (south != MPI_PROC_NULL) {
            MPI_Sendrecv(&u_current[local[0]][1], local[1], MPI_DOUBLE, south, 1, &u_current[local[0] + 1][1],
                         local[1], MPI_DOUBLE, south, 1, MPI_COMM_WORLD, &status);
        }
        if (east != MPI_PROC_NULL) {
            MPI_Sendrecv(&u_current[1][local[1]], 1, column, east, 1, &u_current[1][local[1] + 1], 1, column, east,
                         1, MPI_COMM_WORLD, &status);
        }
        if (west != MPI_PROC_NULL) {
            MPI_Sendrecv(&u_current[1][1], 1, column, west, 1, &u_current[1][0], 1, column, west, 1,
                         MPI_COMM_WORLD, &status);
        }

        BlackSOR(u_previous, u_current, i_min, i_max, j_min, j_max, omega);
        gettimeofday(&tcf, NULL);

        tcomp += (tcf.tv_sec - tcs.tv_sec) + (tcf.tv_usec - tcs.tv_usec) * 0.000001;

#ifdef TEST_CONV
        if (t % C == 0) {
            gettimeofday(&tcvs, NULL);
            converged = converge(u_previous, u_current, i_min, i_max, j_min, j_max);
            MPI_Allreduce(&converged, &global_converged, 1, MPI_INT, MPI_MIN, MPI_COMM_WORLD);
            gettimeofday(&tcvf, NULL);
            tconv += (tcvf.tv_sec - tcvs.tv_sec) + (tcvf.tv_usec - tcvs.tv_usec) * 0.000001;
        }
#endif
    }
    MPI_Barrier(MPI_COMM_WORLD);
    gettimeofday(&ttf, NULL);

    ttotal = (ttf.tv_sec - tts.tv_sec) + (ttf.tv_usec - tts.tv_usec) * 0.000001;

    MPI_Reduce(&ttotal, &total_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&tcomp, &comp_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&tconv, &conv_time, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        U = allocate2d(global_padded[0], global_padded[1]);
        U0_ptr = &(U[0][0]);
    } else {
        U0_ptr = NULL;
    }

    MPI_Gatherv(&u_current[1][1], 1, local_block, U0_ptr, scattercounts, scatteroffset, global_block, 0,
                MPI_COMM_WORLD);

    if (rank == 0) {
        comm_time = total_time - comp_time;
        if (comm_time < 0.0) {
            comm_time = 0.0;
        }

        printf("RedBlackSOR X %d Y %d Px %d Py %d Iter %d ComputationTime %lf TotalTime %lf CommunicationTime %lf ConvergenceTime %lf midpoint %lf\n",
               global[0], global[1], grid[0], grid[1], t, comp_time, total_time, comm_time, conv_time,
               U[global[0] / 2][global[1] / 2]);

#ifdef PRINT_RESULTS
        char *s = malloc(60 * sizeof(char));
        sprintf(s, "resRedBlackSORMPI_%dx%d_%dx%d", global[0], global[1], grid[0], grid[1]);
        fprint2d(s, U, global[0], global[1]);
        free(s);
#endif
    }

    MPI_Finalize();
    return 0;
}
