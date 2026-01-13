#!/bin/bash

## Give the Job a descriptive name
#PBS -N make_kmeans

## Output and error files
#PBS -o naive_results/o.out
#PBS -e naive_results/o.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=1

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a3

RESULTS_DIR="results"

log_dir_for_prog() {
	case "$1" in
		kmeans_seq)
			echo "${RESULTS_DIR}/seq"
			;;
		kmeans_cuda_naive)
			echo "${RESULTS_DIR}/naive"
			;;
		kmeans_cuda_transpose)
			echo "${RESULTS_DIR}/transpose"
			;;
		kmeans_cuda_shared)
			echo "${RESULTS_DIR}/shared_mem"
			;;
		kmeans_cuda_all_gpu)
			echo "${RESULTS_DIR}/all_gpu"
			;;
		kmeans_cuda_all_gpu_single_kernel)
			echo "${RESULTS_DIR}/all_gpu_single_kernel"
			;;
		kmeans_cuda_all_gpu_all_reduction)
			echo "${RESULTS_DIR}/all_gpu_all_reduction"
			;;
		kmeans_cuda_all_gpu_delta_reduction)
			echo "${RESULTS_DIR}/reduction"
			;;
		*)
			echo "${RESULTS_DIR}/other"
			;;
	esac
}

make_clean_out="${RESULTS_DIR}/make_clean.out"
make_clean_err="${RESULTS_DIR}/make_clean.err"

mkdir -p "$RESULTS_DIR"
make clean >> "$make_clean_out" 2>> "$make_clean_err"

progs=(
	kmeans_seq
	kmeans_cuda_naive
	kmeans_cuda_transpose
	kmeans_cuda_shared
	kmeans_cuda_all_gpu
	kmeans_cuda_all_gpu_single_kernel
	kmeans_cuda_all_gpu_all_reduction
	kmeans_cuda_all_gpu_delta_reduction
)

for prog in "${progs[@]}"; do
	log_dir=$(log_dir_for_prog "$prog")
	mkdir -p "$log_dir"
	make_out="${log_dir}/make.out"
	make_err="${log_dir}/make.err"
	make "$prog" >> "$make_out" 2>> "$make_err"
done
