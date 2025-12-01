#!/bin/bash
#PBS -N sync

#PBS -o serial_results/x.serial_8192/1_80_10_10.out
#PBS -e serial_results/x.serial_8192/1_80_10_10.err

#PBS -l nodes=1:ppn=64

#PBS -l walltime=00:20:00

cd /home/parallel/parlab16/shared/a2/conc_ll
export MT_CONF=0
./x.serial 8192 80 10 10
