#!/bin/bash

for dir in */; do
	# remove trailing slash
	dir="${dir%/}"
	PER_LOOP_FILE="per_loop_${dir}.csv"
	TOTAL_FILE="total_${dir}.csv"
	echo "1,2,4,8,16,32,64" > "$PER_LOOP_FILE"
	echo "1,2,4,8,16,32,64" > "$TOTAL_FILE"
	
	per_loop_row=""
	total_row=""
	for i in 1 2 4 8 16 32 64; do
		total=$(awk '/total/ {match($0, /total = *([0-9.]+)/, m); print m[1]}' ${dir}/run_kmeans_$i.out)
		per_loop=$(awk '/per loop/ {match($0, /per loop = *([0-9.]+)/, m); print m[1]}' ${dir}/run_kmeans_$i.out)
		
		total_row+="${total},"
		per_loop_row+="${per_loop},"
	done

	per_loop_row=${per_loop_row%,}
	total_row=${total_row%,}

	# Append rows to the CSVs
	echo "$per_loop_row" >> "$PER_LOOP_FILE"
	echo "$total_row" >> "$TOTAL_FILE"
done
