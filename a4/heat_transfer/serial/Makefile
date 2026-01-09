CC=gcc
CFLAGS=-O3 -lm -Wall
RES=-DPRINT_RESULTS
CONV=-DTEST_CONV

all: jacobi_constant jacobi_converge

jacobi_converge: Jacobi_serial.c utils.c
	$(CC) $(CFLAGS) $(RES) $(CONV) Jacobi_serial.c utils.c -o jacobi_converge

jacobi_constant: Jacobi_serial.c utils.c
	$(CC) $(CFLAGS) $(RES) Jacobi_serial.c utils.c -o jacobi_constant

clean:
	rm jacobi_constant jacobi_converge

