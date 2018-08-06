#!/bin/bash

#### This script will stop the queue processors if they're running
#### and then start them back up again.
####
#### WARNING: If there's currently reduction runs "processing" this may 
#### cause them to get stuck in the "processing" state.

ROOT_DIR="$(dirname "$0")"

## Autoreduction Processor
pkill -9 -f "python .*reduction_processor/reduction_processor_daemon.py start" &&
echo "Stopped reduction_processor_daemon.py";
if [ -e /tmp/reduction_processor_daemon.pid ]
then
    rm /tmp/reduction_processor_daemon.pid && # Removes the tmp pid file
    echo "Removed /tmp/reduction_processor_daemon.pid"
else
    echo ".pid file not found - starting process"
fi
python $ROOT_DIR/reduction_processor/reduction_processor_daemon.py start &&
echo "Started reduction_processor_daemon";

echo ""; # New line


## QueueProcessor
pkill -9 -f "python .*flow_processor/flow_processor_daemon.py start" &&
echo "Stopped flow_processor_daemon";
if [ -e /tmp/flow_processor_daemon.pid ]
then
    rm /tmp/flow_processor_daemon.pid && # Removes the tmp pid file
    echo "Removed /tmp/flow_processor_daemon.pid"
else
    echo ".pid file not found - starting process"
fi
python $ROOT_DIR/flow_processor/flow_processor_daemon.py start &&
echo "Started flow_processor_daemon.py";
