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


class Trace:
    """Creates a trace object """
    def __init__(self, data, plot_style, plot_name, mode=None, error_bars=None):
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

        :param data (dataframe) instrument data in dataframe
        :param error_bars (bool) boolean value to determine if error bars are displayed on not

        :return: trace (dictionary)
        """
        trace = {}
        for axis in list(data.columns):
            if axis == 'E':
                trace['error_y'] = dict(type='data', array=data[axis].to_list(), visible=error_bars)
            else:
                trace[axis.lower()] = data[axis]
        return trace

    @staticmethod
    def _str_to_class(classname):
        """converts string to class object
        :returns: class method object (object) class object converted from string
        """
        return getattr(sys.modules[go.__name__], classname)

    def create_trace(self, data, plot_style, name, error_bars, mode=None):
        """
        Creates a trace

        :param data (dataframe) instrument data in dataframe
        :param plot_style (dictionary) plot styles/types available by plotly
        :param name (string) trace name needs to be unique
        :param error_bars (bool) bool value to determine whether error bars are displayed or not
        :param mode (string) the mode of for a figure - lines, markers, line+markers

        :return: figure (plotly.graph_objs.<plot_style>) trace object using plot_style
        """
        # Make dictionary with string values
        trace = self.trace_dict(data=data, error_bars=error_bars)
        trace['name'] = f"'{name}'"

        if mode:
            trace['mode'] = f"{mode}"

        # Convert string to class retuning plotly plot object
        return self._str_to_class(plot_style)(trace)
