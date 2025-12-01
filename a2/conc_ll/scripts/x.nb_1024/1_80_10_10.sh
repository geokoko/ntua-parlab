#!/bin/bash
#PBS -N sync

#PBS -o results/x.nb_1024/1_80_10_10.out
#PBS -e results/x.nb_1024/1_80_10_10.err

#PBS -l nodes=1:ppn=64

#PBS -l walltime=00:10:00

cd /home/parallel/parlab16/shared/a2/conc_ll
export MT_CONF=0
./x.nb 1024 80 10 10
