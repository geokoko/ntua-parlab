#!/bin/bash

## Give the Job a descriptive name
#PBS -N makejob

## Output and error files
#PBS -o serial_results/o.out
#PBS -e serial_results/e.out

## How many machines should we get?
#PBS -l nodes=1:ppn=1

#PBS -l walltime=00:05:00

cd /home/parallel/parlab16/shared/a4/heat_transfer/serial
make clean
make
