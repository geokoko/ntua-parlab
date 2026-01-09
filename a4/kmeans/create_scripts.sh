#!/bin/bash

# Values of -np you want
for NP in 1 2 4 8 16 32 64
	do
		cat <<EOF > scripts/${NP}.sh
#!/bin/bash

## Give the Job a descriptive name
#PBS -N run_mpi

## Output and error files
#PBS -o results/${NP}.out
#PBS -e results/${NP}.err

## How many machines should we get?
#PBS -l nodes=8:ppn=8

##How long should the job run for?
#PBS -l walltime=00:10:00

module load openmpi/1.8.3
cd /home/parallel/parlab16/shared/a4/kmeans
mpirun -np ${NP} --mca btl tcp,self ./kmeans_mpi -s 256 -n 16 -c 32 -l 10
EOF

chmod +x scripts/${NP}.sh
done
