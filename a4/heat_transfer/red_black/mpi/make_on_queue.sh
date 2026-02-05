#!/bin/bash

#PBS -q parlab
#PBS -N make_rb_mpi
#PBS -o rb_results/make.out
#PBS -e rb_results/make.err
#PBS -l nodes=1:ppn=1
#PBS -l walltime=00:10:00

module load openmpi/1.8.3

cd $HOME/shared/a4/heat_transfer/red_black/mpi
mkdir -p rb_results

make clean
make
