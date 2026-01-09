#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_kmeans

## Output and error files
#PBS -o results/seq.out
#PBS -e results/seq.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a4/kmeans/sequential
./kmeans_seq -s 256 -n 16 -c 32 -l 10
