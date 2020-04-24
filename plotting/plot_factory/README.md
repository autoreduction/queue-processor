# Plot Factory

This directory contains the plot factory, responsible for constructing plot traces, figures to 
return a DashApp for direct insertion into a web-page.

The plot factory should be called using the construct_plot method from within the PlotFactory class 
taking the following arguments:
* plot_meta_file_location
* list of N tuples containing an index_name and dataframe [(name, dataframe)] to construct N figures
* figure name - String containing the instrument name and run number (instrument_run-number)

for example: 
```
dashapp = plot_factory.PlotFactory(
    plot_meta_file_location,
    data,
    figure_name).get_dashapp()
``` 

The dashapp will have the following properties:
* app_id
* app

The plot factory can only insert one figure into one DashApp.

The plot factory has been designed to allow for the future use case of having many figures differing 
in design to be used in one DashApp.

Available plot styles which can be used:
* scattergl
* bar

mode (additional data for a given plot):
* lines
* markers*lines
* 

(Please note that not all mode settings work for all plot types. 
You should refer to [plotly's documentation]: https://plotly.com/r/reference/#scatter-mode)

By default, if no value is associated to plot or mode keys in .yamle config file, a scatter 
line plot will be used.

Below is a UML class diagram segment to visually display the structure of the plot factory:

