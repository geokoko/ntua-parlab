#!/bin/bash
#PBS -N sync

#PBS -o results/x.lazy_1024/8_100_0_0.out
#PBS -e results/x.lazy_1024/8_100_0_0.err

#PBS -l nodes=1:ppn=64

#PBS -l walltime=00:10:00

cd /home/parallel/parlab16/shared/a2/conc_ll
export MT_CONF=0,1,2,3,4,5,6,7
./x.lazy 1024 100 0 0
