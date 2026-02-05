#!/bin/bash

#PBS -q parlab
#PBS -N run_rb_mpi
#PBS -o rb_results/run.out
#PBS -e rb_results/run.err
#PBS -l nodes=8:ppn=8
#PBS -l walltime=02:00:00

set -euo pipefail

module load openmpi/1.8.3

cd $HOME/shared/a4/heat_transfer/red_black/mpi
mkdir -p rb_results

run_tag=$(date +%Y%m%d_%H%M%S)

procs=(1 2 4 8 16 32 64)
px=(1 2 2 4 4 8 8)
py=(1 1 2 2 4 4 8)

# Convergence runs: 512x512, 64 MPI processes, 3 repeats
mkdir -p rb_results/conv_512
for r in 1 2 3; do
  mpirun -np 64 --mca btl tcp,self ./redblacksor_converge 512 512 8 8 >> rb_results/conv_512/mpi_rb_converge_512_p64_${run_tag}_r${r}.out
  echo "---" >> rb_results/conv_512/mpi_rb_converge_512_p64_${run_tag}_r${r}.out
  sleep 1
  done

# Constant-iteration runs (T=256)
for size in 2048 4096 6144; do
  mkdir -p rb_results/const_${size}
  for idx in ${!procs[@]}; do
    np=${procs[$idx]}
    pxv=${px[$idx]}
    pyv=${py[$idx]}
    for r in 1 2 3; do
      mpirun -np $np --mca btl tcp,self ./redblacksor_constant $size $size $pxv $pyv >> rb_results/const_${size}/mpi_rb_constant_${size}x${size}_p${np}_${run_tag}_r${r}.out
      echo "---" >> rb_results/const_${size}/mpi_rb_constant_${size}x${size}_p${np}_${run_tag}_r${r}.out
      sleep 1
    done
  done
  done

