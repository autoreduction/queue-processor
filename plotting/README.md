# Autoreduction Plotting

---

This document provides documentation for the plotting package as part of the Autoreduction project.

Ideal data structure to prepare data into for visualisation:

Create a dataframe that contains a minimum of Spectrum, X and Y axis columns as seen in the 
example below 
- Note additional columns can be used if needed. 

The spectrum should act as the id to distinguish between different sections are data to be plotted 
from one dataframe and can be used to apply pandas group-by functions for more in depth analysis 
of a given spectrum. 

|Spectrum | X      | Y   | E  |
| :---    | :---: |:---:| ---:|
| 1.0     |       |     |     |
| 1.0     | 1     | 2   | 3   |
| 1.0     | 4     | 5   | 6   |
| 2.0     | 1     | 2   | 3   |
| 2.0     | 4     | 5   | 6   |


An example of plotting using this format can be seen in the following github repository inside 
the plotting_multi_spectra_data.py script:
https://github.com/JackEAllen/plotly_as_django_webapp/tree/master/plotting_format_example


The script shows both one method of converting data to this format and one method of plotting of 
this data as part of a Plotly Dash app