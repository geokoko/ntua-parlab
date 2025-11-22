#!/bin/bash
RESULTS=results
SCRIPTS=scripts
mkdir -p $SCRIPTS
mkdir -p $RESULTS

executables=("array_lock" "clh_lock" "critical" "naive" "nosync_lock" "pthread_mutex_lock" "pthread_spin_lock" "tas_lock")
for i in {0..6}; do
	for j in "${executables[@]}"; do
		THREADS=$((2 ** i))
		BINARY="kmeans_omp_$j"
		echo "Running threads: $THREADS for lock: $j"
		mkdir -p ${RESULTS}/$j
		JOBFILE="${SCRIPTS}/run_kmeans_${THREADS}_$j.sh"
		cat > "${JOBFILE}" <<EOF

#!/bin/bash
## Give the Job a descriptive name
#PBS -N run_kmeans_${THREADS}

## Output and error files
#PBS -o ${RESULTS}/$j/run_kmeans_${THREADS}.out
#PBS -e ${RESULTS}/$j/run_kmeans_${THREADS}.err

## How many machines should we get?
#PBS -l nodes=1:ppn=64

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a2/kmeans_locks
export OMP_NUM_THREADS=${THREADS}
export GOMP_CPU_AFFINITY="0-$((THREADS-1))"

./${BINARY} -s 32 -n 16 -c 32 -l 10
EOF

		chmod +x "$JOBFILE"
		qsub -q serial -l nodes=sandman:ppn=64 ${JOBFILE}
	done
	sleep 120
done

