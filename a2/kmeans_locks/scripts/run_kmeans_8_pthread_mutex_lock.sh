
#!/bin/bash
## Give the Job a descriptive name
#PBS -N run_kmeans_8

## Output and error files
#PBS -o results/pthread_mutex_lock/run_kmeans_8.out
#PBS -e results/pthread_mutex_lock/run_kmeans_8.err

## How many machines should we get?
#PBS -l nodes=1:ppn=64

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a2/kmeans_locks
export OMP_NUM_THREADS=8
export GOMP_CPU_AFFINITY="0-7"

./kmeans_omp_pthread_mutex_lock -s 32 -n 16 -c 32 -l 10
