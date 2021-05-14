## queue_processor module

This modules handles the majority of message management in the autoreduction system. It is responsible for the initial creation of the database records for reduction jobs.
This module also handles updating of status's to reduction records as the AMQ message traverses through the system.

The `queue_listener.py` is responsible for ingesting and distributing messages to their correct functions for processing. The `queue_listner` consumes messages from the `/DataReady`, `/ReductionStarted`,`/ReductionComplete`, `/ReductionError` and `/ReductionSkipped` queues. The service is run as a daemon process - as such only runs on Linux.  The daemon process is controlled by `queue_processor_daemon.py`, which produces a command line interface to start/stop/restart the daemon process.
However, the daemon is normally controlled in tandem with the `autoreduction_processor` via the `../restart.sh` script that restarts both these processes.

The process that performs the message management and logic is stored in `handle_message.py`. This contains individual functions that are responsible for each stage of the autoreduction workflow (except for the reduction stage that is handled by the `autoreduction_processor`). The code for this is fairly self documenting, so read the functions and the docstrings in the `handle_message.py` file to learn what each stage is responsible for.
