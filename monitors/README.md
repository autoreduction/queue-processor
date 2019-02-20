# Monitors *(Windows Only)*

Scripts used to check for new runs from the instruments at ISIS.

The `End of Run Monitor` script periodically checks the lastrun.txt file in the ISIS Data archive 
on selected instruments and sends a message to the DataReady queue when runs end.

The `Health check` script is a backup mechanism for the `End of Run Monitor` design to pick up the 
slack should runs be missed. This works on a system of polling and comparing the difference 
between the reduction database and the ISIS cataloguing system (`ICAT`). 

## Windows Installation as a service

Python modules required: pywin32 and stomp.py

1. In an administrative command prompt navigate to the `monitors` folder
1. Run `python ISIS_monitor_win_service.py install`
1. Open Services (again in administrive mode), right click on "Autoreduce Instrument Monitor"
 and select Properties
1. Change Startup Type to Automatic
1. On the 'Log On' tab change to account credentials you wish to use for this process.
1. From the 'Browse...' window select 'Locations...' then fed.cclrc.ac.uk
1. Enter your fedID and click 'Check Names' then 'Ok'
1. Enter your fedID password into both boxes
1. Click Start

Note: The service will have to be restarted at the beginning of a new cycle to pick up the cycle number
