#!/bin/bash

#### This script will stop the queue processors if they're running
#### and then start them back up again.
####
#### WARNING: If there's currently reduction runs "processing" this may 
#### cause them to get stuck in the "processing" state.

pkill -9 -f "python AutoreductionProcessor/autoreduction_processor_daemon.py start" &
python AutoreductionProcessor/autoreduction_processor_daemon.py stop; # Deletes the tmp pid file
echo "Stopped autoreduction_processor_daemon.py";
python AutoreductionProcessor/autoreduction_processor_daemon.py start &
echo "Started autoreduction_processor_daemon";

pkill -9 -f "python QueueProcessor/queue_processor_daemon.py start" &
python QueueProcessor/queue_processor_daemon.py stop;
echo "Stopped queue_processor_daemon";
python QueueProcessor/queue_processor_daemon.py start &
echo "Started queue_processor_daemon.py";

