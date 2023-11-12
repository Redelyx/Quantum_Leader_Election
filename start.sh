#!/bin/sh

for NODES in 2 3 4
do
echo "---------- NODES: $NODES ----------" >> test.txt
python3 main_log_parallel.py $NODES
python3 main_log_sequential.py $NODES
python3 main_linear.py $NODES
done