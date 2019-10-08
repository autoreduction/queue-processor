## AutoreductionProcessor

These scripts handle the messages added to the following queues:
* `/ReductionPending`
* `/ReductionStarted`
* `/RedcutionComplete`
* `/ReductionError`

These scripts focus more on the reduction of the data and are used to control
the reduction jobs that get pushed to the reduction software (at ISIS this is MANTID).