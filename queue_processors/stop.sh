#!/bin/bash

#### This script will stop the queue processors if they're running
####
#### WARNING: If there's currently reduction runs "processing" this may
#### cause them to get stuck in the "processing" state.

ROOT_DIR="$(dirname "$0")"

## Autoreduction Processor
pgrep -f "python.* .*autoreduction_processor/autoreduction_processor_daemon.py start" | xargs kill -9 &&
echo "Stopped autoreduction_processor_daemon.py";
if [ -e /tmp/AutoreduceQueueListenerDaemon.pid ]
then
    rm /tmp/AutoreduceQueueListenerDaemon.pid && # Removes the tmp pid file
    echo "Removed /tmp/AutoreduceQueueListenerDaemon.pid"
fi

echo ""; # New line


## QueueProcessor
pgrep -f "python.* .*queue_processor/queue_listener_daemon.py start" | xargs kill -9 &&
echo "Stopped queue_listener_daemon";
if [ -e /tmp/QueueListenerDaemon.pid ]
then
    rm /tmp/QueueListenerDaemon.pid && # Removes the tmp pid file
    echo "Removed /tmp/QueueListenerDaemon.pid"
fi
