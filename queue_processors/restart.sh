#!/bin/bash

#### This script will stop the queue processors if they're running
#### and then start them back up again.
####
#### WARNING: If there's currently reduction runs "processing" this may 
#### cause them to get stuck in the "processing" state.

ROOT_DIR="$(dirname "$0")"
EXECUTABLE_PATH=$1

## Autoreduction Processor
pkill -9 -f "python3 .*autoreduction_processor/autoreduction_processor_daemon.py start" &&
echo "Stopped autoreduction_processor_daemon.py";
if [ -e /tmp/AutoreduceQueueListenerDaemon.pid ]
then
    rm /tmp/AutoreduceQueueListenerDaemon.pid && # Removes the tmp pid file
    echo "Removed /tmp/AutoreduceQueueListenerDaemon.pid"
else
    echo ".pid file not found - starting process"
fi
if [ $EXECUTABLE_PATH ];
then
    $EXECUTABLE_PATH $ROOT_DIR/autoreduction_processor/autoreduction_processor_daemon.py start &&
    echo "Started autoreduction_processor_daemon";
else
    echo "Using default python";
    python3 $ROOT_DIR/autoreduction_processor/autoreduction_processor_daemon.py start &&
    echo "Started autoreduction_processor_daemon";
fi

echo ""; # New line


## QueueProcessor
pkill -9 -f "python3 .*queue_processor/queue_listener_daemon.py start" &&
echo "Stopped queue_listener_daemon";
if [ -e /tmp/QueueListenerDaemon.pid ]
then
    rm /tmp/QueueListenerDaemon.pid && # Removes the tmp pid file
    echo "Removed /tmp/QueueListenerDaemon.pid"
else
    echo ".pid file not found - starting process"
fi
if [ $EXECUTABLE_PATH ];
then
    $EXECUTABLE_PATH $ROOT_DIR/queue_processor/queue_listener_daemon.py start &&
    echo "Started queue_listener_daemon";
else
    echo "Using default python";
    python3 $ROOT_DIR/queue_processor/queue_listener_daemon.py start &&
    echo "Started queue_listener_daemon";
fi
