#!/bin/bash
#PBS -N sync

#PBS -o results/x.cgl_8192/32_0_50_50.out
#PBS -e results/x.cgl_8192/32_0_50_50.err

#PBS -l nodes=1:ppn=64

#PBS -l walltime=00:10:00

cd /home/parallel/parlab16/shared/a2/conc_ll
export MT_CONF=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
./x.cgl 8192 0 50 50
