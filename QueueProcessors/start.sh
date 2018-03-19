#!/bin/bash
python AutoreductionProcessor/autoreduction_processor_daemon.py stop;
python AutoreductionProcessor/autoreduction_processor_daemon.py start;
python QueueProcessor/queue_processor_daemon.py stop;
python QueueProcessor/queue_processor_daemon.py start;
