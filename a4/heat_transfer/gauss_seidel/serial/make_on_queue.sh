#!/bin/bash

## Give the Job a descriptive name
#PBS -N makejob

## Output and error files
#PBS -o outmakejob
#PBS -e errormakejob

## How many machines should we get?
#PBS -l nodes=1:ppn=64

#PBS -l walltime=00:40:00

## Start 
## Run make in the src folder (modify properly)
cd /home/parallel/parlab16/shared/a4/heat_transfer/gauss_seidel/serial
make clean
make
