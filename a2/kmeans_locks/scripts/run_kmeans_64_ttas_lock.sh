
#!/bin/bash
## Give the Job a descriptive name
#PBS -N run_kmeans_64

## Output and error files
#PBS -o results/ttas_lock/run_kmeans_64.out
#PBS -e results/ttas_lock/run_kmeans_64.err

## How many machines should we get?
#PBS -l nodes=1:ppn=64

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a2/kmeans_locks
export OMP_NUM_THREADS=64
export GOMP_CPU_AFFINITY="0-63"

./kmeans_omp_ttas_lock -s 32 -n 16 -c 32 -l 10
