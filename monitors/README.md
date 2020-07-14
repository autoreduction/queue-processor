# Run Detection *(Any Platform)*

This module contains code for detecting new files from the ISIs Data Cache and  can be run on any platform either standalone on the command line or as a scheduled task. All it requires is a CSV file of the following format:

```
WISH,1234,wish_lastrun.txt,wish_summary.txt,/archive/wish/data,.nxs
GEM,1234,gem_lastrun.txt,gem_summary.txt,/archive/gem/data,.nxs
```

In order, the fields are: instrument name, last run number observed on the instrument 
(without leading zeros), location of this instrument's lastrun.txt, location of this
instrument's summary.txt, data location (parent of cycle folder), file extension of
data to reduce. The last observed run is updated whenever EoRM submits a new run.

There are two settings in settings.py for this script:

* LAST_RUNS_CSV - Location of the CSV file described above
* CYCLE_FOLDER - Folder for the current cycle in the instrument data directory.

## Production Configuration

In production, it is recommended to run this script as a Cron job on Linux or using the task
scheduler on Windows. The period should be a minute or less so that runs are processed
as soon as they arrive.

The cycle folder in settings.py must be updated at the beginning of each new cycle.
