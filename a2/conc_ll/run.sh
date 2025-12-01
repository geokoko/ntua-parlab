#!/bin/bash
RESULTS=results
SCRIPTS=scripts
mkdir -p $SCRIPTS
mkdir -p $RESULTS

executables=("x.serial" "x.cgl" "x.fgl" "x.opt" "x.lazy" "x.nb")
perc_run=("100 0 0" "80 10 10" "20 40 40" "0 50 50")
perc_name=("100_0_0" "80_10_10" "20_40_40" "0_50_50")

for ex in "${executables[@]}"; do
	for list in 1024 8192; do
		DIR="${ex}_${list}"
		mkdir -p ${RESULTS}/$DIR
		mkdir -p ${SCRIPTS}/$DIR
		for i in {0..7}; do
			THREADS=$((2 ** i))
			if (( THREADS <= 32 )); then
				MT_CONF_VAL=$(seq -s, 0 $((THREADS - 1)))
			elif (( THREADS == 64 )); then
				MT_CONF_VAL=$(seq -s, 0 63)
			else  # 128
				MT_CONF_VAL="$(seq -s, 0 63),$(seq -s, 0 63)"
			fi			    
			for j in {0..3}; do
				PERC_N="${perc_name[$j]}"
				PERC_A="${perc_run[$j]}"
				JOBFILE="${SCRIPTS}/${DIR}/${THREADS}_${PERC_N}.sh"
				echo "Running: $ex for $list with $THREADS threads for $PERC_N perc."
				cat > "${JOBFILE}" <<EOF
#!/bin/bash
#PBS -N sync

#PBS -o ${RESULTS}/${DIR}/${THREADS}_${PERC_N}.out
#PBS -e ${RESULTS}/${DIR}/${THREADS}_${PERC_N}.err

#PBS -l nodes=1:ppn=64

#PBS -l walltime=00:10:00

cd /home/parallel/parlab16/shared/a2/conc_ll
export MT_CONF=${MT_CONF_VAL}
./${ex} ${list} ${PERC_A}
EOF
				chmod +x "$JOBFILE"
				qsub -q serial -l nodes=sandman:ppn=64 ${JOBFILE}
			done
		done
		#sleep 400
		while true; do
			read -p "Continue? (y): " ans

			case "$ans" in
				y|Y)
					echo "Continuing with the work"
					break
					;;
				*)
					echo "Not continuing for now"
					;;
			esac
		done
	done
done
