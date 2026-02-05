.KEEP_STATE:
MPICC = mpicc
CFLAGS = -Wall -Wextra -Wno-unused -O3
LDLIBS = -lm

all: seidelsor_constant seidelsor_converge

seidelsor_constant: gauss_seidel_mpi.c utils.o
	$(MPICC) $(CFLAGS) gauss_seidel_mpi.c utils.o -o seidelsor_constant $(LDLIBS)

seidelsor_converge: gauss_seidel_mpi.c utils.o
	$(MPICC) $(CFLAGS) gauss_seidel_mpi.c utils.o -o seidelsor_converge $(LDLIBS) -DTEST_CONV

utils.o: utils.c
	$(MPICC) $(CFLAGS) -c $< -o $@

clean:
	rm -f seidelsor_constant seidelsor_converge utils.o
