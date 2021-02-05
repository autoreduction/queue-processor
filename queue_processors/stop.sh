#!/bin/bash

#### This script will stop the queue processors if they're running
####
#### It will send SIGTERM to allow the queue processor to gracefully close.

ROOT_DIR="$(dirname "$0")"

## QueueProcessor
pkill -15 -f "python3 .*queue_processor/queue_listener_daemon.py start" &&\
    echo -e "\n>>>>>>>>>>>>>> Queue Processor log tail <<<<<<<<<<<<<<" &&\
    tail ../logs/queue_processor.log && echo -e "-----------------------------------------------------\n" &&\
    grep -m 1 "Queue Processor exited gracefully" <(tail -f ../logs/queue_processor.log);
