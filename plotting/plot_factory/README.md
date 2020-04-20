# Plot Factory

This directory contains the plot factory, responsible for constructing plot traces, figures and finally a DashApp.

The plot factory returns a DashApp for direct insertion into a web-page.

The plot factory should be called using the construct_plot method from within the PlotFactory class 
taking the following arguments:
* plot_meta_file_location
* list of N tuples containing an index_name and dataframe [(name, dataframe)] to construct N figures
* figure name - String containing the instrument name and run number (instrument_run-number)

The plot factory can only insert one figure into one DashApp. 

The plot factory has been designed to allow for the future use case of having many figures differing 
in design to be used in one DashApp.

Available plot styles which can be used:
* scatter
* lines
* markers*lines
* bar

By default, if no plot style is passed as argument, a scatter line plot is adopted.

Below is a UML class diagram segment to visually display the structure of the plot factory:

