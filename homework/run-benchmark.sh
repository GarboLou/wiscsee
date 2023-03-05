#!/bin/bash

trap "exit" INT

# change to your own pypy path
pypy=../../../pypy2.7-v7.3.11-linux64/bin/pypy

for mode in small medium
do
	for gh in 0.2 0.3 0.4 0.5 0.6
	do
		for gl in 0.1 0.2 0.3 0.4 0.5
		do
			if (( $(echo "$gh > $gl" |bc -l) )); then
				TS=`date +%Y-%m-%d_%H-%M-%S`
				FOLDER=results/$mode-$gh-$gl
				# check path
				if [ ! -d "$FOLDER" ]; then
					mkdir $FOLDER
				fi
				# run benchmark
				echo "Running with gh=$gh, gl=$gl"
				{ $pypy main.py -m $mode -o $FOLDER -gh $gh -gl $gl ; } &>> $FOLDER/terminal-$TS.log
			fi
		done
	done
done

