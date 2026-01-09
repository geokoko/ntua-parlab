#!/bin/bash

## Give the Job a descriptive name
#PBS -N runjob

## Output and error files
#PBS -o serial_results/serial_converge_3.out
#PBS -e serial_results/serial_converge_3.err

## How many machines should we get?
#PBS -l nodes=1:ppn=1

#PBS -l walltime=00:25:00

cd /home/parallel/parlab16/shared/a4/heat_transfer/serial
./jacobi_converge 512
