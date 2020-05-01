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

# Visualisation Dependencies
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go  # pylint: disable=unused-import

# Internal Dependencies
from plotting.plot_meta_language.interpreter import Interpreter


# Data Dependencies


class PlotFactory:
    """Creates figures from formatted data and layout
       producing a DashApp for direct insertion inside a given web page
       =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
        """

    @staticmethod
    def get_trace_list(data, layout, figure_name):
        """Creates trace list containing traces for each spectrum to place in figure

        :param data
        :param layout
        :param figure_name

        :return object


        """
        trace_list = []
        for spectrum in data.index.unique():

            trace_list.append(Trace(mode=layout.mode,
                                    plot_style=layout.plot_type,
                                    plot_name=f"{figure_name}_{layout.plot_type}",
                                    data=data.loc[spectrum],
                                    error_bars=True).trace)

        return trace_list

    def construct_plot(self, plot_meta_file_location, data, figure_name):
        """Gets DashaApp after calling layout and trace to construct figure in figure factory

           :param plot_meta_file_location (string)
           :param data (pandas dataframe)
           :param figure_name (string)

           :return DashApp (object)
           """

        data.set_index('Spectrum', inplace=True)
        layout = Layout(plot_meta_file_location)
        trace_list = self.get_trace_list(data=data, layout=layout, figure_name=figure_name)
        figure = dict(data=trace_list, layout=layout.layout)

        return DashApp(figure=figure, app_id=figure_name)


class Layout:
    """ Extract Layout as dictionary from interpreted meta data """
    def __init__(self, plot_style):
        """
        :param plot_style (dictionary)
        """
        self.meta_data = plot_style
        self.mode = None
        self.plot_type = None
        self.error_bars = None
        self.layout = self.extract_layout()

    def read_plot_meta_data(self):
        """Use plot interpreter to interpret plot meta data

        :return interpreted_layout (dictionary)
        """
        try:
            interpreted_layout = Interpreter().interpret(self.meta_data)
            return interpreted_layout
        except ImportError as error:
            print(error)
            print(f"Could not Interpret: {self.meta_data}")

    def extract_layout(self):
        """Extracts plot layout data from plot style meta data

        :return self.meta_data (dictionary)
        """
        interpreted_layout = self.read_plot_meta_data()

        if 'mode' in interpreted_layout:
            self.mode = interpreted_layout.pop('mode')
        if 'plot' in interpreted_layout:
            self.plot_type = interpreted_layout.pop('plot')
        return interpreted_layout


class Trace:
    """Creates a trace object """
    def __init__(self, data, plot_style, plot_name, mode=None, error_bars=None): #pylint: disable=too-many-arguments, line-too-long
        """
        :param data (pandas dataframe)
        :param plot_style (dictionary)
        :param plot_name (string)
        :param mode (string)
        :param error_bars (bool)
        """

        self.trace = self.create_trace(mode=mode,
                                       data=data,
                                       plot_style=plot_style,
                                       name=plot_name,
                                       error_bars=error_bars)

    @staticmethod
    def trace_dict(data, error_bars):
        """Creates trace dictionary

        :param data (dataframe)
        :param error_bars (bool)
        """
        trace = {}
        for axis in list(data.columns):
            if axis is 'E':
                if error_bars is True:
                    trace['error_y'] = dict(type='data',
                                            array=data[axis].to_list(),
                                            visible=True)
                # else:
                #     trace[axis.lower()] = f"data['{axis}']"
            else:
                trace[axis.lower()] = f"data['{axis}']"
        return trace

    @staticmethod
    def dict_to_string(trace_dictionary):
        """Converts a dictionary ot a string
        :param trace_dictionary

        :return object
        """

        return ', '.join([f"{key}= {value}" for key, value in trace_dictionary.items()])

    def create_trace(self, data, plot_style, name, error_bars, mode=None): #pylint: disable=too-many-arguments, line-too-long
        """Creates a trace
        :param data (dataframe)
        :param plot_style (dictionary)
        :param name (string)
        :param error_bars (bool)
        :param mode (string)

        :return figure (object)
        """
        # make dictionary with string values
        trace = self.trace_dict(data=data, error_bars=error_bars)
        trace['name'] = f"'{name}'"

        if mode:
            trace['mode'] = f"'{mode}'"

        # make dictionary string
        trace_as_string = self.dict_to_string(trace)

        # perform eval
        return eval(f"go.{plot_style}({trace_as_string})")  # pylint: disable=eval-used


class DashApp:
    """Creates a DashApp for direct insertion into a web page """
    def __init__(self, figure, app_id):  # pylint: disable=too-few-public-methods
        """
        :param figure (dictionary)
        :param app_id (string)
        """
        self.figure = figure
        self.app_id = app_id
        self.app = self.create_dashapp(self.figure, self.app_id)

    @staticmethod
    def create_dashapp(figure, app_id):  # pylint: disable=too-few-public-methods
        """Creates DashApp

           :return DashApp (object) DashApp object for direct insertion into webapp
        """
        app = dash.Dash()
        app.layout = html.Div([
            html.Div(
                dcc.Graph(
                    id=app_id,  # Unique ID to track DashApp
                    figure=figure
                )
            )
        ])
        return app
