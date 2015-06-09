End of Run Script
==========

This script periodically checks the lastrun.txt file on selected instruments and sends a message to the DataReady queue when runs end.

## Windows Installation as a service

1. In an administrative command prompt navigate to the autoreduce_webapp folder
2. `python ISIS_monitor_win_service.py install`
3. Open Services, right click on "Autoreduce Instrument Monitor" and select Properties
4. Change Startup Type to Automatic
5. On the 'Log On' tab change to 'This Account'
6. From the 'Browse...' window select 'Locations...' then fed.cclrc.ac.uk
7. Enter your fedID and click 'Check Names' then 'Ok'
8. Enter your fedID password into both boxes
9. Click Start


