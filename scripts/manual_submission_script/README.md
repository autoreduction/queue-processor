# Manual Submission Script
This script is used to manually submit jobs to the autoreduction service. You can submit either a single run or a range of runs for reduction.

## Set up
1. Ensure that `utils/settings.py` is using the correct credentials for the task you wish to perform.

## Running
#### Single Run
When you want to submit a single datafile/run for reduction.
```
$ python manual-submission.py [Instrument Name] [Run Number]
```
Example:
```
$ python manual-submission.py WISH 40421
```

#### Range Run
When you want to submit multiple contiguous datafiles/runs for reduction.
```
$ python manual-submission.py [Instrument Name] [Start Run Number] -e [End Run Number]
```
Example:
```
$ python manual-submission.py WISH 40421 -e 40425
```