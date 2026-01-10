#!/bin/bash
OUTDIR=results
SCRIPTDIR=scripts
mkdir -p $OUTDIR
mkdir -p $SCRIPTDIR

for i in {0..6}; do
	if [ "$i" -eq 0 ]; then
		BINARY="kmeans_seq"
	else
		BINARY="kmeans_omp_reduction"
	fi

	THREADS=$((2 ** i))
	echo "Running threads: $THREADS"
	JOBFILE="$SCRIPTDIR/openmp_${THREADS}.sh"

	cat > "$JOBFILE" <<EOF
#!/bin/bash
## Give the Job a descriptive name
#PBS -N kmeans_${THREADS}

## Output and error files
#PBS -o ${OUTDIR}/openmp_${THREADS}.out
#PBS -e ${OUTDIR}/openmp_${THREADS}.err

## How many machines should we get?
#PBS -l nodes=1:ppn=${THREADS}

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/shared/a4/kmeans/openmp-kmeans
export OMP_NUM_THREADS=${THREADS}
export GOMP_CPU_AFFINITY="0-$((THREADS-1))"

./${BINARY} -s 256 -n 16 -c 32 -l 10
EOF
	chmod +x "$JOBFILE"
	qsub -q serial -l nodes=sandman:ppn=64 ${JOBFILE}
done
