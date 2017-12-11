# Data Reduction WebApp

## What it is 

A web-based front-end system to display information about jobs run on the auto-reduction server.

## Requirements 

### Essential User Requirements

* Security constraints imposed to ensure only staff and team members can access runs.
* Link to data files and reduced files.
* Ability to resubmit jobs.
* Ability to modify script variables through the interface.
* Modify user variables and additional advanced variables (such as whitebeam run number)
* Have the option to save to experiment storage location on "Rutherford"
* Display which script a run is using
* Batch runs that all use the same script variables

### Essential System Requirements

* Listen for ActiveMQ topic messages and respond accordingly
* Validate the script can have its variables modified
* Utilise existing authentication systems
* No Python code exposed
* Users only see relevant instruments/experiments based on their permissions

### Nice-to-have

* Provide details for each run from ICAT.
* Provide a network path for files when within STFC network or an ICAT download URL when outside.
* Link off to the instrument data - [http://dataweb.isis.rl.ac.uk/Dashboards](http://dataweb.isis.rl.ac.uk/Dashboards)
* Usable on desktops, mobiles and tablets.
* Reduce number of clicks required when use only have one instrument/experiment (by going straight to the runs)

## What the system is not

This is not intended to be an instrument monitoring system or experiment run log. 
It doesn't need to collect process variables from the instruments. 