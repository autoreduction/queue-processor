# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Constructs a plot and DashApp object for insertion into directly into a web page
"""

#  TODO - Add Error bars to trace; Unit tests, look into best way to get plot style.

# Internal dependencies
from plotting.plot_meta_language.interpreter import Interpreter

# Core dependencies
import pandas as pd

# Visualisation dependencies
import dash
import dash_core_components as dcc
import dash_html_components as html


class PlotFactory:
    """Creates figures from formatted data and layout
       producing a DashApp for direct insertion inside a given web page"""

    def __init__(self, plot_meta_file_location, data, figure_name):
        """Initialises Plot Factory attributes"""
        self.layout = Interpreter().interpret(plot_meta_file_location)
        self.data = data
        self.figure_name = figure_name

    def construct_figure_list(self):
        """Constructs figure to be placed in DashApp
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
            :returns List of figures
            """

        # Temporary storage of figures
        figures_list = []  # Allows for N figures to be added a DashApp

        # For a given data name and dataframe, create figure
        for data_object in self.data:
            # Send data object to FigureFactory and append figure to figures_list
            figures_list.append(FigureFactory(self.figure_name, self.layout, data_object))
        return figures_list

    def construct_plot(self):
        """Creates DashApp instance for a given number of figures
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
            :returns
            ----------
            DashApp (object) - DashApp for direct insertion into web-page
        """

        return DashApp(figure=self.construct_figure_list(), app_id=self.figure_name)


class Layout:
    """ Extract Layout as dictionary from interpreted meta data
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
        :returns
        ----------
        layout (dictionary) - Plotly figure layout
    """

    def __init__(self, interpreted_meta_language):
        """ Retrieves interpreted meta data about plot
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
        """
        self.interpreted_meta_language = interpreted_meta_language

    def layout_keys(self):
        """Extract Layout keys from interpreted meta data
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
           :returns
           ----------
           dictionary keys (list) Extracted layout from interpreted data
         """
        keys_list = []
        for key in self.interpreted_meta_language.keys():
            if key is not 'type':  # type key refers to figure styles, not layout
                keys_list.append(key)
        return keys_list

    def layout(self):
        """Returns plot Layout from interpreted meta data
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
           :returns
           ----------
           layout (dictionary) - Plot layout
        """
        # Layout dictionary
        return {x: self.interpreted_meta_language[x] for x in self.layout_keys()}


class FigureFactory:
    """Converts a data object containing N traces into a figure
       =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
    """

    def __init__(self, figure_title, layout, data_object):
        """initialises figure name, data name and data
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
           :parameter
            ----------
             figure_title (string) figure title (instrument_run_number
             layout (dictionary) layout dictionary
             data_object (list of tuples)  [(index_name and dataframe), ~N]
        """
        self.title = figure_title
        self.layout = layout
        self.data = data_object

    def construct_trace(self):
        """constructs a list of traces to be added to figure
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
           :returns
           ----------
           trace_list (list) list of traces-
        """
        trace_list = []

        # For spectrum in data, create trace
        for spectrum in self.data:
            trace_list.append(Trace(mode=self.layout['type'],
                                    data=self.data,
                                    plot_style=self.layout['type']).trace)
        return trace_list

    def create_figure(self):
        """Constructs a figure from dataframe and layout
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
           :returns
            ----------
            Figure (dictionary)
        """
        figure = dict(data=self.construct_trace(),
                      layout=Layout(self.layout).layout())

        return figure


class Trace:
    """Creates a trace object
       =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
    """

    def __init__(self, mode, data, plot_style=None, trace=None):
        """Initialises values to construct a trace object
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
        """
        self.mode = mode
        self.axis_list = list(self.data.columns)
        self.name, self.data = data
        # Default plot style if not provided is scatter. See README.md to view available plot styles
        if plot_style is not None:
            self.style = plot_style
        else:
            self.style = 'scatter'

        self.trace = self.create_trace()

    def create_trace(self):
        """Creates trace object
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
           :returns
            ----------
            trace (dictionary) - Plot trace for insertion into figure
        """
        # Add plot axis to trace
        trace = {}
        for axis in list(self.data.columns):
            trace[axis] = self.data[axis]

        trace['name'] = f"{self.name}_{self.mode}"  # plot name
        trace['mode'] = self.mode  # type of plot
        return trace


class DashApp:
    """Creates a DashApp for direct insertion into a web page
       =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
    """

    def __init__(self, figure, app_id):
        """Initialises values to construct a DashApp
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
        """
        self.app_id = app_id
        self.figures = figure

    def create_dashapp(self):
        """Creates DashApp
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
           :returns
           ----------
           DashApp (object) DashApp object for direct insertion into webapp
        """
        app = dash.Dash()
        app.layout = html.Div([
            html.Div(
                dcc.Graph(
                    id=self.app_id,  # Unique ID to track DashApp
                    figure=self.figures
                )
            )
        ])
        return app
