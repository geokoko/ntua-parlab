#!/bin/bash

## Give the Job a descriptive name
#PBS -N validate_kmeans

## Output and error files
#PBS -o results_validate/validate.out
#PBS -e results_validate/validate.err

## How many machines should we get?
#PBS -l nodes=1:ppn=40

##How long should the job run for?
#PBS -l walltime=00:30:00

## Start
## Run validation in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a3

set -euo pipefail

RESULTS_DIR="results_validate"

sizes='64'
coordinates='32'
centers='64'
loop_threashold='10'
block_size='64'

progs=(
	kmeans_cuda_naive
	kmeans_cuda_transpose
	kmeans_cuda_shared
	kmeans_cuda_all_gpu
	kmeans_cuda_all_gpu_single_kernel
	kmeans_cuda_all_gpu_delta_reduction
	kmeans_cuda_all_gpu_all_reduction
)

mkdir -p "$RESULTS_DIR"

make clean >> "${RESULTS_DIR}/make_clean.out" 2>> "${RESULTS_DIR}/make_clean.err"
make VALIDATE_FLAG=-DVALIDATE kmeans_seq >> "${RESULTS_DIR}/make_seq.out" 2>> "${RESULTS_DIR}/make_seq.err"
for prog in "${progs[@]}"; do
	make VALIDATE_FLAG=-DVALIDATE "$prog" >> "${RESULTS_DIR}/make_${prog}.out" 2>> "${RESULTS_DIR}/make_${prog}.err"
done

for size in $sizes; do
	for coord in $coordinates; do
		for center in $centers; do
			prefix="Sz-${size}_Coo-${coord}_Cl-${center}"
			./kmeans_seq -s $size -n $coord -c $center -l $loop_threashold >> "${RESULTS_DIR}/${prefix}_seq.out" 2>> "${RESULTS_DIR}/${prefix}_seq.err"
			for prog in "${progs[@]}"; do
				for bs in $block_size; do
					out_file="${RESULTS_DIR}/${prefix}_${prog}_Bs-${bs}.out"
					err_file="${RESULTS_DIR}/${prefix}_${prog}_Bs-${bs}.err"
					./${prog} -s $size -n $coord -c $center -l $loop_threashold -b $bs >> "$out_file" 2>> "$err_file"
				done
			done
		done
	done
done
