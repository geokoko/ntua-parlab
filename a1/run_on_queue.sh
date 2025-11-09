#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_game_of_life

## Output and error files
#PBS -o output_files/8p_shared.out
#PBS -e output_files/error.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=8

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

module load openmp
cd /home/parallel/parlab16/shared/a1
export OMP_NUM_THREADS=8
./game_of_life 200 200
