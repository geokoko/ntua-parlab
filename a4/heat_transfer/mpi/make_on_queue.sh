#!/bin/bash

## Give the Job a descriptive name
#PBS -N make_jacobi

## Output and error files
#PBS -o jac_results/o.out
#PBS -e jac_results/e.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:05:00

module load openmpi/1.8.3
cd /home/parallel/parlab16/shared/a4/heat_transfer/mpi
make clean
make
