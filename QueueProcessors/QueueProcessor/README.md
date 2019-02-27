## QueueProcessor

These scripts handle the messages added to the following queues:
* `/DataReady`
* `/ReductionComplete`
* `/ReductionError`

As well as this, the Queue processor is the interface between the message queues and
the autoreduction database. More specifically it creates the dataobject for each run,
and updates it's status as it progresses through pipeline of the system.