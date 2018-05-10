#!/bin/bash

#### This script will stop the queue processors if they're running
#### and then start them back up again.
####
#### WARNING: If there's currently reduction runs "processing" this may 
#### cause them to get stuck in the "processing" state.

pkill -9 -f "python AutoreductionProcessor/autoreduction_processor_daemon.py start" &&
echo "Stopped autoreduction_processor_daemon.py";
rm /tmp/AutoreduceQueueProcessorDaemon.pid && # Removes the tmp pid file
echo "Removed /tmp/AutoreduceQueueProcessorDaemon.pid"
python AutoreductionProcessor/autoreduction_processor_daemon.py start &&
echo "Started autoreduction_processor_daemon";

echo ""; # New line

pkill -9 -f "python QueueProcessor/queue_processor_daemon.py start" &&
echo "Stopped queue_processor_daemon";
rm /tmp/QueueProcessorDaemon.pid && # Removes the tmp pid file
echo "Removed /tmp/QueueProcessorDaemon.pid"
python QueueProcessor/queue_processor_daemon.py start &&
echo "Started queue_processor_daemon.py";