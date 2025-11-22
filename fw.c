/*
 * Standard implementation of the Floyd-Warshall Algorithm
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include "util.h"

inline int min(int a, int b);

void save_all_values(int **A, int N, const char *filename)
{
    FILE *fp = fopen(filename, "w");
    if (!fp) {
	perror("Failed to open file");
	return;
    }

    int i, j;
    for (i = 0; i < N; i++) {
	for (j = 0; j < N; j++) {
	    if (i == j) continue;
	    fprintf(fp, "dist(%d -> %d) = %d\n", i, j, A[i][j]);
	}
    }
    fclose(fp);
}

int main(int argc, char **argv)
{
	int **A;
	int i,j,k;
	struct timeval t1, t2;
	double time;
	int N=1024;

	if (argc != 3) {
		fprintf(stdout,"Usage: %s N output_file\n", argv[0]);
		exit(0);
	}

	N=atoi(argv[1]);

	A = (int **) malloc(N*sizeof(int *));
	for(i=0; i<N; i++) A[i] = (int *) malloc(N*sizeof(int));

	graph_init_random(A,-1,N,128*N);

	gettimeofday(&t1,0);
	for(k=0;k<N;k++)
		for(i=0; i<N; i++)
			for(j=0; j<N; j++)
				A[i][j]=min(A[i][j], A[i][k] + A[k][j]);

	gettimeofday(&t2,0);
	save_all_values(A, N, argv[2]);
	time=(double)((t2.tv_sec-t1.tv_sec)*1000000+t2.tv_usec-t1.tv_usec)/1000000;
	printf("FW,%d,%.4f\n", N, time);

	/*
	for(i=0; i<N; i++)
		for(j=0; j<N; j++) fprintf(stdout,"%d\n", A[i][j]);
	*/

	return 0;     
}

inline int min(int a, int b)
{
	if(a<=b)return a;
	else return b;
}

