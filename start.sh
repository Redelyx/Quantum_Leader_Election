#!/bin/sh

for NODES in 2 3 4 5 6 7 8 9 10 11 12 13 14 15
do
echo "---------- NODES: $NODES ----------" >> test.txt
python3 main_log_parallel.py $NODES
python3 main_log_sequential.py $NODES
python3 main_linear.py $NODES
done