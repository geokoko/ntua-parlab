#!/bin/bash

## Give the Job a descriptive name
#PBS -N game_of_life_make

## Output and error files
#PBS -o output_files/make.out
#PBS -e output_files/error_make.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

module load openmp
cd /home/parallel/parlab16/shared/a1
make clean
make

