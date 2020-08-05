## autoreduction_processor module

This Daemon handles the management of processes and the processes themselves that perform the reduction of the data.

The `autoreduction_processor.py` is responsible for the management of redcution processes. It is run as a linux Daemon using `autoreduction_processor_daemon.py` as a control script to start/stop/restart the daemon process. As it is a daemon it can only be run in linux environments. The daemon is normally started with the `queue_processor.py` daemon via the `../restart.sh` script. 

The `autoreduction_processor` itself is an ActiveMQ consumer that is implemented using the stomp library. It consumes messages from the `/ReductionPending` queue and starts a new python instance running `post_process_admin.py` for each valid message it reads from the queue.

`post_proces_admin.py` is the script that is responsible for the actual reduction of data. The *main* responsiblities of the script are:
* Sending a message to `/ReductionStarted` to update the status of the job in the database (from *queued* to *started*)
* Fetching the reduction script
* Setting up reduction environment
  * Creating a temporary directory for resulting reduced data
  * Redirecting logging information
* Starting the reduction process in external software (such as `Mantid`)
* Handling what happens after the reduction process has ended:
  * If the job was successful and no errors occured
    * Copy reduced data to its long term storage directory (at ISIS this is on CEPH)
    * Send a message to `/RedcutionComplete`
  * If the job was unsuccessful (Any errors were raised, exceptions thrown)
    * Send a message to `/ReductionError`
  * The job should be skipped. Reasons for skipping a run are: the run does not require reduction, the instrument is running in an unknown mode of operation, the reduction script does not support the type of data it was given (e.g. event mode on EnginX)
    * Send a message to `ReductionSkipped`
    * *Note: skipped runs are also identified earlier than this stage if it is found there is an issue with the RB numbers, e.g. calibration runs (a RB number is a number that uniquely identify an ISIS experimental proposal. However, sometimes data are collected which are not associated with any specific ISIS proposal, such as to calibrate the beamline or other beamline maintenance/diagnosis tasks)*

Once all of the above is completed, the process will terminate and be cleaned up by `autoreduction_processor.py` which should be tracking the PID of this process so it can be deleted.
