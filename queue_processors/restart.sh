#!/bin/bash

#### This script will stop the queue processors if they're running
#### and then start them back up again.
####
#### It will send SIGTERM to allow the queue processor to gracefully close.

ROOT_DIR="$(dirname "$0")"
EXECUTABLE_PATH=$1

## QueueProcessor
pkill -15 -f "python3 .*queue_processor/queue_listener_daemon.py start" &&\
    echo -e "\n>>>>>>>>>>>>>> Queue Processor log tail <<<<<<<<<<<<<<" &&\
    tail ../logs/queue_processor.log && echo -e "-----------------------------------------------------\n" &&\
    grep -m 1 "Queue Processor exited gracefully" <(tail -f ../logs/queue_processor.log);

if [ $EXECUTABLE_PATH ];
then
    $EXECUTABLE_PATH $ROOT_DIR/queue_processor/queue_listener_daemon.py start &&
    echo "Started queue_listener_daemon";
else
    echo "Using default python";
    python3 $ROOT_DIR/queue_processor/queue_listener_daemon.py start &&
    echo "Started queue_listener_daemon";
fi
