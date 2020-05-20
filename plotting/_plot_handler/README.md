# Plot Handler

This script acts as a controller for the plot functionality, responsible for:
* Getting the plot file via SFTP client
* Getting the associated plot meta data file
* Instructing the plotting factory using a unique figure name (Instrument_Run_Number) to build 
a Dashapp for direct insertion in to the Autoreduction web-app

## Notes
The figure_name is the name which will need to be referenced in run_summary template 
django dash object as `````{%plotly_app name="<figure_name>"%}`````

For plot factory usage, please see `plotting/plot_factory/README.md` for more details.