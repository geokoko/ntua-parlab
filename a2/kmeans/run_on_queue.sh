#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_kmeans

## Output and error files
#PBS -o ex_output/run_kmeans.out
#PBS -e ex_output/run_kmeans.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/koko/shared/ask2/kmeans
export OMP_NUM_THREADS=1
./kmeans_seq -s 50 -n 3 -c 4 -l 10
