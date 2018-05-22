ISIS Autoreduction - monitors
=============================

Here are all the services that are used to monitor the ISIS data archive as well as tests for those services.

The two monitors are currently:
* End of Run monitor
* Archive Monitor

## End of Run monitor

This script periodically checks the lastrun.txt file on selected instruments and sends a message to the DataReady queue when runs end.

## Archive monitor

The archive monitor periodically polls the isis data archive to check for any files that were not found by the End of Run monitor

## Installation

Python modules required: pywin32 and stomp.py

1. Edit the LOG_FILE location in the script to point to a sensible directory
2. In an administrative command prompt navigate to the autoreduce_webapp folder
3. `python isis_monitor_win_service.py install`
4. Open Services, right click on "Autoreduce Instrument Monitor" and select Properties
5. Change Startup Type to Automatic
6. On the 'Log On' tab change to 'This Account'
7. From the 'Browse...' window select 'Locations...' then fed.cclrc.ac.uk
8. Enter your fedID and click 'Check Names' then 'Ok'
9. Enter your fedID password into both boxes
10. Click Start

*Note: The same process applies to the archive monitor*
