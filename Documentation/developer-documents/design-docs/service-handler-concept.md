Justification
-------------
As the autoreduction project continues to grow, there is a growing need to be able to monitor
not only the overall service but individual elements more closely. The will aide not only in debugging,
and automatically fixinf issues, but potentential contribute to load balancing when we have additioanl
processing machines.

Design
------
The service handler could be an entirely separate git repo (and may make sense as a stand-alone project).
If implemented in this context, then the service handler would allow the user to add the following:
* Service - the name and location of the service as well as how to access it
* Service type - what sort of service is it? Activemq, python win service, python daemon
* Service recovery action - A script to recover the service should it go offline
* Service post-reset actions - Anything that should be done after a restart of the script 


Proposed implementation
-----------------------
This should be a python program that to begin with could take a JSON input for each of the above, 
but later could have a GUI to show service health etc.


Priority - Medium
Deadline - Required before we have additional nodes
