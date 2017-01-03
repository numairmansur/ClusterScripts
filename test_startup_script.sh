#!/bin/bash

#redirect the output to the following file:
#$ -o /home/kleinaa/output 


#redirect the error messages to the following file:
#$ -e /home/kleinaa/output


echo "hello from job script!"
echo "the date is" `date`
echo "here's /etc/hosts contents:"
echo "my name is numair"
echo "finishing job :D"