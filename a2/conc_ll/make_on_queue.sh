#!/bin/bash

## Give the Job a descriptive name
#PBS -N make_sync

## Output and error files
#PBS -o o.out
#PBS -e e.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a2/conc_ll
make clean
make
