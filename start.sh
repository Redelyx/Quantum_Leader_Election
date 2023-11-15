#!/bin/sh

$NODES = 3
echo "---------- NODES: $NODES ----------" >> test.txt
python3 main_log_parallel.py 5 50
python3 main_log_parallel.py 5 50
python3 main_log_parallel.py 5 50
python3 main_log_parallel.py 5 50
python3 main_log_parallel.py 5 50



