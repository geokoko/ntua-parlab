#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_kmeans

## Output and error files
#PBS -o naive_results/naive.out
#PBS -e naive_results/naive.err

## How many machines should we get? 
#PBS -l nodes=1:ppn=40

##How long should the job run for?
#PBS -l walltime=02:00:00

## Start 
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a3
export CUDA_VISIBLE_DEVICES=2

RESULTS_DIR="results"

log_dir_for_prog() {
	case "$1" in
		kmeans_seq)
			echo "${RESULTS_DIR}/seq"
			mkdir -p "${RESULTS_DIR}/seq"
			;;
		kmeans_cuda_naive)
			echo "${RESULTS_DIR}/naive"
			mkdir -p "${RESULTS_DIR}/naive"
			;;
		kmeans_cuda_transpose)
			echo "${RESULTS_DIR}/transpose"
			mkdir -p "${RESULTS_DIR}/transpose"
			;;
		kmeans_cuda_shared)
			echo "${RESULTS_DIR}/shared_mem"
			mkdir -p "${RESULTS_DIR}/shared_mem"
			;;
		kmeans_cuda_all_gpu)
			echo "${RESULTS_DIR}/all_gpu"
			mkdir -p "${RESULTS_DIR}/all_gpu"
			;;
		kmeans_cuda_all_gpu_delta_reduction)
			echo "${RESULTS_DIR}/reduction"
			mkdir -p "${RESULTS_DIR}/reduction"
			;;
		*)
			echo "Unknown program: $1"
			exit 1
	esac
}

run_logged() {
	local prog="$1"
	local bs="$2"
	local log_dir
	local prefix
	local out_file
	local err_file

	log_dir=$(log_dir_for_prog "$prog")
	mkdir -p "$log_dir"

	prefix="Sz-${size}_Coo-${coord}_Cl-${center}"
	if [ -n "$bs" ]; then
		prefix="${prefix}_Bs-${bs}"
	fi

	out_file="${log_dir}/${prefix}.out"
	err_file="${log_dir}/${prefix}.err"

	if [ -n "$bs" ]; then
		./${prog} -s $size -n $coord -c $center -l $loop_threashold -b $bs >> "$out_file" 2>> "$err_file"
	else
		./${prog} -s $size -n $coord -c $center -l $loop_threashold >> "$out_file" 2>> "$err_file"
	fi
}
# sizes='32 64 128 256 512 1024 2048'
# only test 1024 for now
sizes='1024'

# coordinates='2 4 8 16 32'
# question only ask for 2 and 32
coordinates='2 32'

#centers='64'
# only test 64 for now
centers='64'

loop_threashold='10'
# loop_threashold='100''

block_size='32 48 64 128 256 512 1024'

progs=(
	kmeans_seq
	kmeans_cuda_naive
	kmeans_cuda_transpose
	kmeans_cuda_shared
	#kmeans_cuda_all_gpu
	#kmeans_cuda_all_gpu_delta_reduction
)

for size in $sizes; do
	for coord in $coordinates; do
		for center in $centers; do
			filename=Execution_logs/Sz-${size}_Coo-${coord}_Cl-${center}.csv 
			echo "Implementation,blockSize,av_loop_t,min_loop_t,max_loop_t" >> $filename
			for prog in "${progs[@]}"; do
				case "$prog" in
					kmeans_seq)
						run_logged "$prog"
						;;
					kmeans_cuda_naive|kmeans_cuda_transpose|kmeans_cuda_shared|kmeans_cuda_all_gpu|kmeans_cuda_all_gpu_delta_reduction)
						for bs in $block_size; do
							run_logged "$prog" "$bs"
						done
						;;
					*)
						echo "Unknown program: $prog"
						;;
				esac
			done
		done
	done
done
