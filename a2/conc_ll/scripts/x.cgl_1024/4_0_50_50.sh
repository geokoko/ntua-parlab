#!/bin/bash
#PBS -N sync

#PBS -o results/x.cgl_1024/4_0_50_50.out
#PBS -e results/x.cgl_1024/4_0_50_50.err

#PBS -l nodes=1:ppn=64

#PBS -l walltime=00:10:00

cd /home/parallel/parlab16/shared/a2/conc_ll
export MT_CONF=0,1,2,3
./x.cgl 1024 0 50 50
