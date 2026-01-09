#!/bin/bash

# Give the Job a descriptive name
#PBS -N run_jacobi_mpi

## Output and error files
#PBS -o jac_results/run.out
#PBS -e jac_results/run.err

## How many machines should we get?
#PBS -l nodes=8:ppn=8

##How long should the job run for?
#PBS -l walltime=00:40:00

module load openmpi/1.8.3
cd /home/parallel/parlab16/shared/a4/heat_transfer/mpi

mpirun -np  1 --mca btl tcp,self ./jacobi_constant 2048 2048 1 1 1>>./jac_results/2048/mpi_jacobi_constant_1.out
mpirun -np  2 --mca btl tcp,self ./jacobi_constant 2048 2048 2 1 1>>./jac_results/2048/mpi_jacobi_constant_2.out
mpirun -np  4 --mca btl tcp,self ./jacobi_constant 2048 2048 2 2 1>>./jac_results/2048/mpi_jacobi_constant_4.out
mpirun -np  8 --mca btl tcp,self ./jacobi_constant 2048 2048 4 2 1>>./jac_results/2048/mpi_jacobi_constant_8.out
mpirun -np 16 --mca btl tcp,self ./jacobi_constant 2048 2048 4 4 1>>./jac_results/2048/mpi_jacobi_constant_16.out
mpirun -np 32 --mca btl tcp,self ./jacobi_constant 2048 2048 8 4 1>>./jac_results/2048/mpi_jacobi_constant_32.out
mpirun -np 64 --mca btl tcp,self ./jacobi_constant 2048 2048 8 8 1>>./jac_results/2048/mpi_jacobi_constant_64.out

mpirun -np  1 --mca btl tcp,self ./jacobi_constant 4096 4096 1 1 1>>./jac_results/4096/mpi_jacobi_constant_1.out
mpirun -np  2 --mca btl tcp,self ./jacobi_constant 4096 4096 2 1 1>>./jac_results/4096/mpi_jacobi_constant_2.out
mpirun -np  4 --mca btl tcp,self ./jacobi_constant 4096 4096 2 2 1>>./jac_results/4096/mpi_jacobi_constant_4.out
mpirun -np  8 --mca btl tcp,self ./jacobi_constant 4096 4096 4 2 1>>./jac_results/4096/mpi_jacobi_constant_8.out
mpirun -np 16 --mca btl tcp,self ./jacobi_constant 4096 4096 4 4 1>>./jac_results/4096/mpi_jacobi_constant_16.out
mpirun -np 32 --mca btl tcp,self ./jacobi_constant 4096 4096 8 4 1>>./jac_results/4096/mpi_jacobi_constant_32.out
mpirun -np 64 --mca btl tcp,self ./jacobi_constant 4096 4096 8 8 1>>./jac_results/4096/mpi_jacobi_constant_64.out

mpirun -np  1 --mca btl tcp,self ./jacobi_constant 6144 6144 1 1 1>>./jac_results/6144/mpi_jacobi_constant_1.out
mpirun -np  2 --mca btl tcp,self ./jacobi_constant 6144 6144 2 1 1>>./jac_results/6144/mpi_jacobi_constant_2.out
mpirun -np  4 --mca btl tcp,self ./jacobi_constant 6144 6144 2 2 1>>./jac_results/6144/mpi_jacobi_constant_4.out
mpirun -np  8 --mca btl tcp,self ./jacobi_constant 6144 6144 4 2 1>>./jac_results/6144/mpi_jacobi_constant_8.out
mpirun -np 16 --mca btl tcp,self ./jacobi_constant 6144 6144 4 4 1>>./jac_results/6144/mpi_jacobi_constant_16.out
mpirun -np 32 --mca btl tcp,self ./jacobi_constant 6144 6144 8 4 1>>./jac_results/6144/mpi_jacobi_constant_32.out
mpirun -np 64 --mca btl tcp,self ./jacobi_constant 6144 6144 8 8 1>>./jac_results/6144/mpi_jacobi_constant_64.out

mpirun -np 64 --mca btl tcp,self ./jacobi_converge 512 512 8 8 1>>./jac_results/mpi_jacobi_converge.out
