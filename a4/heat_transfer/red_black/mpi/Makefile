.KEEP_STATE:
MPICC = mpicc
CFLAGS = -Wall -Wextra -Wno-unused -O3
LDLIBS = -lm

all: redblacksor_constant redblacksor_converge

redblacksor_constant: red_black_mpi.c utils.o
	$(MPICC) $(CFLAGS) red_black_mpi.c utils.o -o redblacksor_constant $(LDLIBS)

redblacksor_converge: red_black_mpi.c utils.o
	$(MPICC) $(CFLAGS) red_black_mpi.c utils.o -o redblacksor_converge $(LDLIBS) -DTEST_CONV

utils.o: utils.c
	$(MPICC) $(CFLAGS) -c $< -o $@

clean:
	rm -f redblacksor_constant redblacksor_converge utils.o
