# Manual Operations
These scripts are used to perform operations manually with autoreduction.
Currently this includes submitting a new run or deleting an existing run.
When using any of these scripts please ensure that your settings are correct before use:
* Enter the correct ICAT and ActiveMQ login details into `utils/credentials.ini`.

## Manual Submission
#### Single Run
When you want to submit a single datafile/run for reduction.
```
$ python manual_submission.py [Instrument Name] [Run Number]
```
Example:
```
$ python manual_submission.py WISH 40421
```

#### Range Run
When you want to submit multiple contiguous datafiles/runs for reduction.
```
$ python manual_submission.py [Instrument Name] [Start Run Number] -e [End Run Number]
```
Example:
```
$ python manual_submission.py WISH 40421 -e 40425
```

## Manual Remove
**USE WITH CAUTION**: This is a DESTRUCTIVE script and will PERMANENTLY REMOVE a run and
 it's meta data from the reduction database.
#### Single Run
When you want to remove a single datafile/run for reduction.
```
$ python manual_remove.py [Instrument Name] [Run Number]
```
Example:
```
$ python manual_remove.py WISH 40421
```

If multiple run versions are available, then enter the run version(s) that you want to remove. 
To remove multiple run versions you need to input a comma separated list or a range of versions. 
E.g. `0, 1, 2` or `0 - 2`.

*Note: Whilst runs are removed from the database, the reduce data will still remain on CEPH*
