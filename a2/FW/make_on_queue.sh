#!/bin/bash

## Give the Job a descriptive name
#PBS -N make_fw

## Output and error files
#PBS -o outputs/o.out
#PBS -e outputs/e.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:01:00

cd /home/parallel/parlab16/shared/a2/FW
make clean
make
