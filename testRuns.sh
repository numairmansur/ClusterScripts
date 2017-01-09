#!/bin/bash

#redirect the output to the following file:
#$ -o /home/mansurm/output 


#redirect the error messages to the following file:
#$ -e /home/mansurm/output

echo "running python script now:"
python /home/mansurm/ClusterScripts/testPython.py
echo "runnin successful"
