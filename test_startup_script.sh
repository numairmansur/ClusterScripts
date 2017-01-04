#!/bin/bash

#redirect the output to the following file:
#$ -o /home/mansurm/output 


#redirect the error messages to the following file:
#$ -e /home/mansurm/output

echo HOME=$HOME
echo USER=$USER
echo JOB_ID=$JOB_ID
echo JOB_NAME=$JOB_NAME
echo HOSTNAME=$HOSTNAME
echo SGE_TASK_ID=$SGE_TASK_ID


# activate the virtual environment:
source spearmintlite/bin/activate
