# Autoreduction Plotting

Documentation for the plotting package as part of the Autoreduction project.

## Data structure to prepare data for visualisation

- Create a dataframe that contains a minimum of Spectrum, X and Y axis columns as seen in the 
example below 
    - Note additional columns can be used if needed. 

The spectrum column should act as the id to distinguish between different sections of data to be 
plotted from one dataframe and can be used to apply pandas group-by functions for more in depth 
analysis of a given spectrum. 

|Spectrum | X      | Y   | E   |
| :---    | :---:  |:---:| ---:|
| 1       |        |     |     |
| 1       | 1      | 2   | 3   |
| 1       | 4      | 5   | 6   |
| 2       | 1      | 2   | 3   |
| 2       | 4      | 5   | 6   |


An example of plotting using this format can be seen in the following github repository inside 
the plotting_multi_spectra_data.py script:
https://github.com/JackEAllen/plotly_as_django_webapp/tree/master/plotting_format_example

This code is kept in a separate repository due to it's size, meaning it would not align with the 
rest of the project. 

The script shows one method of converting data to this format and one method of plotting data of 
this format as part of a Plotly Dash app.
