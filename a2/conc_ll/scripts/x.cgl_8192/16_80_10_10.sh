#!/bin/bash
#PBS -N sync

#PBS -o results/x.cgl_8192/16_80_10_10.out
#PBS -e results/x.cgl_8192/16_80_10_10.err

#PBS -l nodes=1:ppn=64

#PBS -l walltime=00:10:00

cd /home/parallel/parlab16/shared/a2/conc_ll
export MT_CONF=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
./x.cgl 8192 80 10 10
