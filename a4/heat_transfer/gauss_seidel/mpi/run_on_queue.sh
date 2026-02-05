#PBS -N run_gauss_mpi

## Output and error files
#PBS -o run_gauss_mpi.out
#PBS -e run_gauss_mpi.err

## How many machines should we get?
#PBS -l nodes=8:ppn=8

##How long should the job run for?
#PBS -l walltime=01:20:00

## Start
## Load appropriate module
module load openmpi/1.8.3


# cd to the directory where the qsub command was issued
cd $HOME/shared/a4/heat_transfer/gauss_seidel/mpi

# Clear the output file
mkdir -p results
#> ./results/gauss_mpi.out
#> ./results/gauss_mpi_conv.out

for size in 2048 4096 6144
	do
		        mpirun -np  1 --mca btl tcp,self ./seidelsor_constant $size $size 1 1 1>>./results/gauss_heat_transfer_mpi.out
			        mpirun -np  2 --mca btl tcp,self ./seidelsor_constant $size $size 2 1 1>>./results/gauss_heat_transfer_mpi.out
				        mpirun -np  4 --mca btl tcp,self ./seidelsor_constant $size $size 2 2 1>>./results/gauss_heat_transfer_mpi.out
					        mpirun -np  8 --mca btl tcp,self ./seidelsor_constant $size $size 4 2 1>>./results/gauss_heat_transfer_mpi.out
						        mpirun -np 16 --mca btl tcp,self ./seidelsor_constant $size $size 4 4 1>>./results/gauss_heat_transfer_mpi.out
							        mpirun -np 32 --mca btl tcp,self ./seidelsor_constant $size $size 8 4 1>>./results/gauss_heat_transfer_mpi.out
								        mpirun -np 64 --mca btl tcp,self ./seidelsor_constant $size $size 8 8 1>>./results/gauss_heat_transfer_mpi.out
									done

#CONV TEST
mpirun -np 64 --mca btl tcp,self ./seidelsor_converge 512 512 8 8 1>>./results/gauss_heat_transfer_mpi_CONV.out
