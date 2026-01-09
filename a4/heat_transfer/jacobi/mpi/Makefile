.KEEP_STATE:
MPICC = mpicc
CFLAGS = -Wall -Wextra -Wno-unused -O3
LDLIBS = -lm

all: jacobi_constant jacobi_converge

jacobi_constant: jacobi_mpi.c utils.o
	$(MPICC) $(CFLAGS) jacobi_mpi.c utils.o -o jacobi_constant $(LDLIBS)

jacobi_converge: jacobi_mpi.c utils.o
	$(MPICC) $(CFLAGS) jacobi_mpi.c utils.o -o jacobi_converge $(LDLIBS) -DTEST_CONV

utils.o: utils.c
	$(MPICC) $(CFLAGS) -c $< -o $@

clean:
	rm -f jacobi_constant jacobi_converge utils.o