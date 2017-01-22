template = """#!/bin/bash
#$ -S /bin/bash
#$ -o %s -e %s
#$ -cwd
#$ -m n
#$ -t %d-%d
jobs_file="%s"

echo "Here's what we know from the SGE environment"
echo SHELL=$SHELL
echo HOME=$HOME
echo USER=$USER
echo JOB_ID=$JOB_ID
echo JOB_NAME=$JOB_NAME
echo HOSTNAME=$HOSTNAME
echo SGE_TASK_ID=$SGE_TASK_ID
echo jobs_file=${jobs_file}
line=`head -n $SGE_TASK_ID "${jobs_file}" | tail -1`   # Get line of todoFilename.
echo Calling: bash -c "$line"                                  #output

%s

echo "Job started at: `date`"

echo
bash -c "$line"
echo

echo "Job finished with exit code $? at: `date`" 

echo DONE

%s
"""

from argparse import ArgumentParser
import datetime
from functools import partial
import os
from os.path import expanduser
from Queue import Queue, Empty
import signal
import sys
import subprocess
from threading import Thread
import time

parser = ArgumentParser()
parser.add_argument("jobfile", metavar="Job file", nargs=1, help="A file with one job per line")
parser.add_argument("--startup", help="A file with bash commands to be copied to the .pbs file before the calling command.")
parser.add_argument("--shutdown", help="A file with bash commands to be copied to the .pbs file after the calling command.")
group = parser.add_mutually_exclusive_group()
group.add_argument("--cores", type=int,
                    help="Number of cores per job for qaad_pe. Must not be specified if a queue is specified.")
group.add_argument("-q", "--queue", type=str, choices=["meta_gpu-tf.q", "meta_gpu-rz.q", "aad_core.q", "aad_pe.q", "meta_core.q", "test_core.q"], help="Queue to submit job to. Must not be specified if the number of cores is specified.")
group.add_argument("--local", type=int, metavar="JOB_ID",
                   help="Run the job local instead of submitting it via qsub. "
                   "This can be useful for testing or running small/fast jobs on the local machine.")
parser.add_argument("--lr", action="store_const", const=True, 
                    help="Flag indicating a job with a runtime > 5000s (1h23m)")
parser.add_argument("--max50", action="store_const", const=True,
                    help="Submit the jobs to a resource which allows the execution on only 50 cores")
parser.add_argument("--max100", action="store_const", const=True,
                    help="Submit the jobs to a resource which allows the execution on only 100 cores")
parser.add_argument("--array_min", default=None, type=int, help="Index of first subjob.")
parser.add_argument("--array_max", default=None, type=int, help="Index of last subjob.")
parser.add_argument("-n", "--dry-run", const=True, action="store_const",
                    help="Print pbs file and submission command to the terminal instead of executing the job")
parser.add_argument("-o", "--output", default=os.path.join(expanduser("~"), "sgein"),
                    help="Output directory of the generated .pbs file")
parser.add_argument("-l", "--logfiles", default=os.path.join(expanduser("~"), "sgeout"),
                    help="Output directory of the log files of the job")
                    
args = parser.parse_args()

if args.queue in ("meta_gpu-tf.q", "meta_gpu-rz.q") and args.lr:
    raise ValueError("Submitting to %s and indicating a long run is not possible" % (args.queue, args.lr))

out_folder = args.logfiles
if not os.path.isdir(out_folder):
    try:
        os.mkdir(out_folder)
    except:
        sys.stderr.write("Failed to create folder: %s" %(out_folder))
    
if not os.path.isdir(args.output):
    try:
        os.mkdir(args.output)
    except:
        sys.stderr.write("Failed to create folder: %s" %(args.output))

# Read startup shell script
startup = ""
if args.startup:
    with open(args.startup) as fh:
        startup = "".join(fh.readlines())
        
# Read shutdown shell script
shutdown = ""
if args.shutdown:
    with open(args.shutdown) as fh:
        shutdown = "".join(fh.readlines())

# Find out the number of jobs
num_jobs = 0
with open(args.jobfile[0]) as fh:
    lines = fh.readlines()
    num_jobs = len(lines)
    
if args.array_min is None:
    start_array_jobs_at = 1
else:
    start_array_jobs_at = max(1, args.array_min)
    
if args.array_max is None:
    end_array_jobs_at = num_jobs
else:
    end_array_jobs_at = min(num_jobs, args.array_max)

# Create the pbs file
pbs = template % (out_folder, out_folder, start_array_jobs_at, end_array_jobs_at, args.jobfile[0], startup, shutdown)
    
local_time = datetime.datetime.today()
time_string = "%d-%d-%d--%d-%d-%d-%d" % (local_time.year, local_time.month,
    local_time.day, local_time.hour, local_time.minute,
    local_time.second, local_time.microsecond)
    
jobfile_filename = os.path.split(args.jobfile[0])[1]
output_file = os.path.join(args.output, "%s_%s.pbs" % (jobfile_filename, time_string))

if not args.dry_run:
    with open(output_file, "w") as fh:
        fh.write(pbs)
    os.chmod(output_file, 0750)
else:
    print pbs


if not args.local:
    # Find out submission command
    submission_prolog = """{ { id | egrep "\(aad\)|\(aad-hiwi\)" > /dev/null; } || { echo ""; echo "Error: You are not a member of the AAD-Group"; echo ""; exit 1; } } 2>&1
    id | egrep "\(aad\)" > /dev/null && gruppe='aad'
    id | egrep "\(aad-hiwi\)" > /dev/null && gruppe='aad-hiwi'

    newgrp $gruppe <<EONG
    """ 
    submission_command = "qsub -notify"
    if args.cores:
        if 17 > args.cores > 1:
            submission_command += " -l own -q aad_pe.q -pe pe_aad %d" % args.cores
        else:
            raise ValueError("Number of cores (slots) must be > 1 and < 17, is %d" % args.cores)
    elif args.queue:
        if args.queue in ["aad_core.q", "aad_pe.q"]:
            submission_command += " -l own"
        submission_command += " -q %s" % args.queue
    else:
        submission_command += " -l own -q aad_core.q"

    if args.lr:
        submission_command += " -l lr=1"
    if args.max50:
        submission_command += " -l max50=1"
    if args.max100:
        submission_command += " -l max100=1"
        
    submission_command += " " + output_file
    submission_epilog = "\nEONG\nexit\nnewgrp\nexit"
        
    # Submit the job
    if not args.dry_run:
        print submission_command
        cmd = submission_prolog + submission_command + submission_epilog
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, shell=True, executable="/bin/bash")
        stdoutdata, stderrdata = proc.communicate()
        if stdoutdata:
            print stdoutdata
        if stderrdata:
            print stderrdata
    else:
        print
        print submission_command

else:
    execution_command = "for i in {%d..%d};\n" \
                        "  do echo '################################################################################\n'" \
                        "  echo \"Starting iteration ${i}\"\n" \
                        "  echo '################################################################################\n'" \
                        "  mkdir /tmp/%d.${i}.aad_core.q;\n" \
                        "  export SGE_TASK_ID=${i};\n" \
                        "  export JOB_ID=%d;\n" \
                        "  bash -c \"%s\";\n" \
                        "  rm /tmp/%d.${i}.aad_core.q -rf;\n" \
                        "done" % (start_array_jobs_at, end_array_jobs_at, 
                        args.local, args.local, output_file, args.local)
                        
    def enqueue_output(out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()
        
    def signal_callback(signal_, frame, pid):
        os.killpg(pid, signal.SIGTERM)
        exit()
    
    if not args.dry_run:
        proc = subprocess.Popen(execution_command, stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, shell=True, executable="/bin/bash",
               preexec_fn=os.setsid)
        callback = partial(signal_callback, pid=proc.pid)
        signal.signal(signal.SIGINT, callback)
                                
        stderr_queue = Queue()
        stdout_queue = Queue()
        stderr_thread = Thread(target=enqueue_output, args=(proc.stderr, stderr_queue))
        stdout_thread = Thread(target=enqueue_output, args=(proc.stdout, stdout_queue))
        stderr_thread.daemon = True
        stdout_thread.daemon = True
        stderr_thread.start()
        stdout_thread.start()
        
        while True:
            if proc.poll() is not None:
                break
            time.sleep(1)
            
            try:
                while True:
                    line = stdout_queue.get_nowait()
                    sys.stdout.write(line)
                    sys.stdout.flush()
            except Empty:
                pass

            try:
                while True:
                    line = stderr_queue.get_nowait()
                    sys.stderr.write("[ERR]:" + line)
                    sys.stderr.flush()
            except Empty:
                pass
    else:
        print
        print execution_command
            
