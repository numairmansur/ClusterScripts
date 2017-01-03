#!/bin/bash

#redirect the output to the following file:
#$ -o /home/mansurm/sgeout 


#redirect the error messages to the following file:
#$ -e /home/mansurm/sgeout

echo HOME=$HOME
echo USER=$USER
echo JOB_ID=$JOB_ID
echo JOB_NAME=$JOB_NAME
echo HOSTNAME=$HOSTNAME
echo SGE_TASK_ID=$SGE_TASK_ID


