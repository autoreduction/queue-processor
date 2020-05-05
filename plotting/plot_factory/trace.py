# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Constructs a plot and DashApp object for insertion into directly into a web page
"""

# Core Dependencies
import plotly.graph_objects as go  # pylint: disable=unused-import


class Trace:
    """Creates a trace object """
    def __init__(self, data, plot_style, plot_name, mode=None, error_bars=None): #pylint: disable=too-many-arguments, line-too-long
        """
        Trace Object
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
        """
        Creates trace dictionary

        :param data (dataframe)
        :param error_bars (bool)

        :return: trace (dictionary)
        """
        trace = {}
        for axis in list(data.columns):
            if axis == 'E':
                trace['error_y'] = dict(type='data',
                                        array=data[axis].to_list(),
                                        visible=error_bars)
            else:
                trace[axis.lower()] = f"data['{axis}']"
        return trace

    @staticmethod
    def dict_to_string(trace_dictionary):
        """
        Converts a dictionary ot a string

        :param trace_dictionary

        :return: trace object (object)
        """

        return ', '.join([f"{key}= {value}" for key, value in trace_dictionary.items()])

    def create_trace(self, data, plot_style, name, error_bars, mode=None): #pylint: disable=too-many-arguments, line-too-long
        """
        Creates a trace

        :param data (dataframe)
        :param plot_style (dictionary)
        :param name (string)
        :param error_bars (bool)
        :param mode (string)

        :return: figure (object)
        """
        # Make dictionary with string values
        trace = self.trace_dict(data=data, error_bars=error_bars)
        trace['name'] = f"'{name}'"

        if mode:
            trace['mode'] = f"'{mode}'"

        # Convert dictionary to string
        trace_as_string = self.dict_to_string(trace)

        # Perform eval
        return eval(f"go.{plot_style}({trace_as_string})")  # pylint: disable=eval-used

