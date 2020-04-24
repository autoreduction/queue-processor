# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Constructs a plot and DashApp object for insertion into directly into a web page
"""

# TODO: Allow for mode and plot to not exist in yaml file and plot to still be displayed.
# Note pandas and plotly.graph_objs dependencies are used, but not recognised by pycharm interpreter

# Internal Dependencies
from plotting.plot_meta_language.interpreter import Interpreter

# Data Dependencies
import pandas as pd

# Visualisation Dependencies
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go


class PlotFactory:
    """Creates figures from formatted data and layout
       producing a DashApp for direct insertion inside a given web page
       =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

        """
    def __init__(self, plot_meta_file_location, data, figure_name):
        """

        Parameters
        ----------
        plot_meta_file_location (string)
        data (pandas dataframe)
        figure_name (string)
        """
        self.style = Interpreter().interpret(plot_meta_file_location)
        self.data = data
        self.data.set_index('Spectrum', inplace=True)
        self.data_labels = self.data.index.unique()

        self.figure_name = figure_name

    def get_trace_list(self, layout):
        """Creates trace list containing traces for each spectrum to place in figure

        Parameters
        ----------
        layout (object)
        """
        trace_list = []
        for spectrum in self.data_labels:

            trace_list.append(Trace(mode=layout.mode,
                                    plot_style=layout.plot_type,
                                    plot_name=f"{self.figure_name}_{layout.plot_type}",
                                    data=self.data.loc[spectrum],
                                    error_bars=True).trace)

        return trace_list

    def construct_plot(self):
        """Gets DashaApp after calling layout and trace to construct figure in figure factory
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

           Returns
           ----------
           DashApp (object)
           """
        layout = Layout(self.style)
        trace_list = self.get_trace_list(layout=layout)
        figure = dict(data=trace_list, layout=layout.layout)

        return DashApp(figure=figure, app_id=self.figure_name)


class Layout:
    """ Extract Layout as dictionary from interpreted meta data
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
        :returns
        ----------
        lay
    """
    def __init__(self, plot_style):
        """

        Parameters
        ----------
        plot_style (dictionary)

        """
        self.meta_data = plot_style
        self.mode = None
        self.plot_type = None
        self.error_bars = None
        self.layout = self.extract_layout(self.meta_data)

    def extract_layout(self, plot_type):
        """Extracts plot layout data from plot style meta data

        Parameters
        ----------
        plot_type

        Returns
        ----------
        self.meta_data (dictionary)

        """
        if self.meta_data['mode']:
            self.mode = self.meta_data.pop('mode')
        if self.meta_data['plot']:
            self.plot_type = self.meta_data.pop('plot')
        return self.meta_data


class Trace:
    """Creates a trace object
       =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
    """
    def __init__(self, data, plot_style, plot_name, mode=None, error_bars=None):
        """

        Parameters
        ----------
        data (pandas dataframe)
        plot_style (dictionary)
        plot_name (string)
        mode (string)
        error_bars (bool)
        """
        self.trace = self.create_trace(mode=mode,
                                       data=data,
                                       plot_style=plot_style,
                                       name=plot_name,
                                       error_bars=error_bars)

    @staticmethod
    def trace_dict(data, error_bars):
        """makes trace dictionary

        Parameters
        ----------
        data (dataframe)
        error_bars (bool)
        """
        trace = {}
        for axis in list(data.columns):
            if error_bars is True:
                if axis is 'E':
                    trace['error_y'] = dict(type='data',
                                            array=data[axis].to_list(),
                                            visible=True)
                else:
                    trace[axis.lower()] = f"data['{axis}']"
            else:
                trace[axis.lower()] = f"data['{axis}']"
        return trace

    def create_trace(self, data, plot_style, name, error_bars, mode=None):
        """creates a trace

        Parameters
        ----------
        data (dataframe)
        plot_style (dictionary)
        name (string)
        error_bars (bool)
        mode (string)
        """
        # make dictionary with string values
        trace = self.trace_dict(data=data, error_bars=error_bars)
        trace['name'] = f"'{name}'"

        if mode:
            trace['mode'] = f"'{mode}'"

        # make dictionary string
        trace_as_string = ', '.join([f"{key}= {value}" for key, value in trace.items()])

        # perform eval
        return eval(f"go.{plot_style}({trace_as_string})")


class DashApp:
    """Creates a DashApp for direct insertion into a web page
       =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
    """
    def __init__(self, figure, app_id):
        """

        Parameters
        ----------
        figure (dictionary)
        app_id (string)
        """
        self.figure = figure
        self.app_id = app_id
        self.app = self.create_dashapp()

    def create_dashapp(self):
        """Creates DashApp
           =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
           Returns
           ----------
           DashApp (object) DashApp object for direct insertion into webapp
        """
        app = dash.Dash()
        app.layout = html.Div([
            html.Div(
                dcc.Graph(
                    id=self.app_id,  # Unique ID to track DashApp
                    figure=self.figure
                )
            )
        ])
        return app


