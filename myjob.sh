#!/bin/bash
#$ -q aad_core
#$ -cwd
#$ -o output_file_name
#$ -e error_file_name


virtualenv -p /usr/bin/python2.7 venv
source venv/bin/activate
pip install scipy
pip install numpy
pip install protobuf
git clone https://github.com/JasperSnoek/spearmint.git
cd spearmint
cd spearmint
cd spearmint
python setup.py install
export PYTHONPATH='~/spearmint/spearmint/'
cd ..
cd ..
cd ..
git clone https://github.com/numairmansur/HPOlib2.git
cd HPOlib2
python setup.py install

COPY CSV FILES FOR SAVING THE RESULTS

RUN:
python main.py --driver=local --method=GPEIOptChooser --method-args=noiseless=1 /home/numair/Music/spearmint/spearmint/examples/bohachevsky5/config.pb
