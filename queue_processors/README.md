# Processors for queues *(Linux only)*

Scripts that perform the main flow control in the system by ingesting and sending messages from the messenging server, ActiveMQ.
This handles the ActiveMQ queues and is the section of the code that deals with reduction.

Service components of Autoreduction can in general be setup on more than one OS (platform). However, the Queue procesors must be run on linux based systems due to it's implementation of daemons. We have so far not be presented with a need to run this service component on another platform.

As of this writing two processors are used to handle, setup and listen to the different ActiveMQ queues Autoreduction needs. Details of these can be found in the subdirectories of this folder and in the READMEs of these folders.

To start the two queue processors run:
```
$ ./restart.sh
```


## Local Setup

- Ensure `utils/settings.py` is setup (see readme in Utils)
- Copy `build/ansible-compute/roles/queue_processors/templates/qp_settings.py.j2`
  to `QueueProcessors/QueueProcessor/settings.py`