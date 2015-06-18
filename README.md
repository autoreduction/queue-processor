End of Run Script
==========

This script periodically checks the lastrun.txt file on selected instruments and sends a message to the DataReady queue when runs end.

## Windows Installation as a service

Python modules required: pywin32 and stomp.py

1. Edit the LOG_FILE location in the script to point to a sensible directory
2. In an administrative command prompt navigate to the autoreduce_webapp folder
3. `python ISIS_monitor_win_service.py install`
4. Open Services, right click on "Autoreduce Instrument Monitor" and select Properties
5. Change Startup Type to Automatic
6. On the 'Log On' tab change to 'This Account'
7. From the 'Browse...' window select 'Locations...' then fed.cclrc.ac.uk
8. Enter your fedID and click 'Check Names' then 'Ok'
9. Enter your fedID password into both boxes
10. Click Start

Note: The service will have to be restarted at the beginning of a new cycle to pick up the cycle number
