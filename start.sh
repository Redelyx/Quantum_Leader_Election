#!/bin/sh

for NODES in 2 3 4 5 6
do
echo "---------- NODES: $NODES ----------" >> test.txt
python3 main_log_parallel.py $NODES 600
done

