Justification
-------------
As the autoreduction project continues to grow, there is a growing need to be able to monitor not only the overall service but individual elements more closely. The will aide not only in debugging, and automatically fixing issues, but potentential contribute to load balancing when we have additioanl processing machines.

Requirements
------------
* The system must be completely non-intrusive to the workflow of autoreduction e.g. the service (whether that
be ActiveMQ, QueueProcessors, End of Run Monitor etc.) should be unaware of the service handler monitoring it.

* The system should show the current status of each service:
  * Starting
  * Live
  * Restarting
  * Down

* The system should be able to interact with each service to either query it's current status or restart the service if required

* Produce information about when (and if known) how the service went down.

Design
------
### Individual Service handler
Each service should have a handler which could be an extension of the current `utils/clients`. This should be able to do the following:
* Start the service
* Stop the service
* Restart (Stop then Start) the service
* Get the current status of the service
It should be possible to send and receive messages from the service handlers (perhaps a web API)

### Service controller
The service controller/monitor is designed to first monitor all the current services that it knows about and display their status and secondly be able to interact with those services such as reseting they (or other dependant services) stop running. This should be possible to do by hand or automatically.
* Monitor services
* Restart services
  * Manually
  * Automatically

Proposed implementation
-----------------------
1. Change the clients to use `ServiceHandlers` as described in `Individual Service handler`
2. Change processes (e.g. QueueProcessor, End of run monitor) to use `ServiceHandlers` as described in `Individual Service handler`
3. Ensure these service can be reset via web API (or choosen tech)
4. Create a service controller that will show the status of each service 
5. Allow the service controller to Manually access the Web API for the services
6. Have services automatically restart if they go down
7. Allow for automatic workflows to be restarted e.g. if service A goes down: restart service A, B and C




Priority - Medium

Deadline - Required before we have additional nodes
