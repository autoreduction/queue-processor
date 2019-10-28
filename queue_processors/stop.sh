#!/bin/bash

#### This script will stop the queue processors if they're running
####
#### WARNING: If there's currently reduction runs "processing" this may
#### cause them to get stuck in the "processing" state.

ROOT_DIR="$(dirname "$0")"

## Autoreduction Processor
pgrep -f "python.* .*autoreduction_processor/autoreduction_processor_daemon.py start" | xargs kill -9 &&
echo "Stopped autoreduction_processor_daemon.py";
if [ -e /tmp/AutoreduceQueueProcessorDaemon.pid ]
then
    rm /tmp/AutoreduceQueueProcessorDaemon.pid && # Removes the tmp pid file
    echo "Removed /tmp/AutoreduceQueueProcessorDaemon.pid"
fi

echo ""; # New line


## QueueProcessor
pgrep -f "python.* .*queue_processor/queue_processor_daemon.py start" | xargs kill -9 &&
echo "Stopped queue_processor_daemon";
if [ -e /tmp/QueueProcessorDaemon.pid ]
then
    rm /tmp/QueueProcessorDaemon.pid && # Removes the tmp pid file
    echo "Removed /tmp/QueueProcessorDaemon.pid"
fi
