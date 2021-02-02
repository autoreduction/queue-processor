#!/bin/bash

#### This script will stop the queue processors if they're running
####
#### WARNING: If there's currently reduction runs "processing" this WILL
#### cause them to get stuck in the "processing" state as it will also stop the reduction runner!

ROOT_DIR="$(dirname "$0")"

read -p "Are you sure you want to KILL the queue_processor? Have you tried restart.sh first? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    pkill -9 -f "python3 .*queue_processor/queue_listener_daemon.py start";
fi
