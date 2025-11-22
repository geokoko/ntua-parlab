#!/bin/bash
OUTDIR=outputs/s4096
SCRIPTDIR=scripts/s4096
mkdir -p $OUTDIR
mkdir -p $SCRIPTDIR

BINARY="fw_sr"
BSIZES=(16 32 64 128)


for i in {0..6}; do
	THREADS=$((2 ** i))
	echo "Running threads: $THREADS"
	for B in "${BSIZES[@]}"; do
		JOBFILE="$SCRIPTDIR/${THREADS}_B${B}.sh"
		cat > "$JOBFILE" <<EOF
#!/bin/bash
## Give the Job a descriptive name
#PBS -N fw

## Output and error files
#PBS -o ${OUTDIR}/4096_${THREADS}_B${B}.out
#PBS -e ${OUTDIR}/4096_${THREADS}_B${B}.err

## How many machines should we get?
#PBS -l nodes=1:ppn=${THREADS}

##How long should the job run for?
#PBS -l walltime=00:10:00

## Start
## Run make in the src folder (modify properly)

cd /home/parallel/parlab16/oar/FW
export OMP_NUM_THREADS=${THREADS}
export GOMP_CPU_AFFINITY="0-$((THREADS-1))"

./${BINARY} 4096 ${B}
EOF

		chmod +x "$JOBFILE"
		qsub -q serial -l nodes=sandman:ppn=64 ${JOBFILE}
	done
done
