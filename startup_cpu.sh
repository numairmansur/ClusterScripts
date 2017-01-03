#! /bin/bash


#redirect the output to the following file:
#$ -o /home/kleinaa/sgeout 


#redirect the error messages to the following file:
#$ -e /home/kleinaa/sgeout



echo HOME=$HOME
echo USER=$USER
echo JOB_ID=$JOB_ID
echo JOB_NAME=$JOB_NAME
echo HOSTNAME=$HOSTNAME
echo SGE_TASK_ID=$SGE_TASK_ID

export THEANO_FLAGS=floatX=float64,nvcc.fastmath=True,force_device=True,device=cpu,cuda.root=/usr/local/cuda,exception_verbosity=high,compiledir=/tmp/${JOB_ID}.${SGE_TASK_ID}.meta_cpu/

source $HOME/virtualenv/local/bin/activate

