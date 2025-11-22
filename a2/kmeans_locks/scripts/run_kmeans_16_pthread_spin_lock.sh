
#!/bin/bash
## Give the Job a descriptive name
#PBS -N run_kmeans_16

## Output and error files
#PBS -o results/pthread_spin_lock/run_kmeans_16.out
#PBS -e results/pthread_spin_lock/run_kmeans_16.err

## How many machines should we get?
#PBS -l nodes=1:ppn=64

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a2/kmeans_locks
export OMP_NUM_THREADS=16
export GOMP_CPU_AFFINITY="0-15"

./kmeans_omp_pthread_spin_lock -s 32 -n 16 -c 32 -l 10
