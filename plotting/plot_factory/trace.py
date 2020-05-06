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
import sys
import plotly.graph_objects as go  # pylint: disable=unused-import


class Trace:  # pylint: disable=too-many-arguments, line-too-long
    """Creates a trace object """
    def __init__(self, data, plot_style, plot_name, mode=None, error_bars=None):  # pylint: disable=too-many-arguments, line-too-long
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
                trace[axis.lower()] = data[axis]
        return trace
    
    @staticmethod
    def _str_to_class(classname):
        """converts string to class object
        :returns: class method object (object) class object converted from string
        """
        return getattr(sys.modules[go.__name__], classname)

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
            trace['mode'] = f"{mode}"

        # print(trace)

        # Convert dictionary to string
        # trace_as_string = self.dict_to_string(trace)

        # Perform eval
        plot_type_class_object = self._str_to_class(plot_style)
        plot = plot_type_class_object(trace)
        return plot
        # return eval(f"go.{plot_style}({trace_as_string})")  # pylint: disable=eval-used
