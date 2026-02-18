#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_mpi

## Output and error files
#PBS -o run_mpi_helloworld.out
#PBS -e run_mpi_helloworld.err

## How many machines should we get? 
#PBS -l nodes=8:ppn=8

module load openmpi/1.8.3
cd <YOUR_SCIROUTER_PATH>/a4/kmeans 
mpirun -np 1 --mca btl tcp,self ./kmeans_mpi -s 256 -n 16 -c 32 -l 10
