# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Constructs a plot and DashApp object for insertion into directly into a web page
"""

# Internal Dependencies

from plotting.plot_factory.layout import Layout
from plotting.plot_factory.trace import Trace
from plotting.plot_factory.dashapp import DashApp


class PlotFactory:
    """
    Creates figures from formatted data and layout
    producing a DashApp for direct insertion inside a given web page
    """
    @staticmethod
    def create_trace_list(data, layout):
        """
        Creates trace list containing traces for each spectrum to place in figure
        :param data (pandas dataframe) instrument data placed in pandas dataframe
        :param layout (plotting.plot_factory.Layout) object containing plot layout attributes

        :return: trace_list (list of trace objects)
        """
        trace_list = []
        for spectrum in data.index.unique():

            trace_list.append(
                Trace(mode=layout.mode,
                      plot_style=layout.plot_type,
                      plot_name=f"{spectrum}_{layout.plot_type}",
                      data=data.loc[spectrum],
                      error_bars=layout.error_bars).trace)

        return trace_list

    def create_plot(self, plot_meta_file_location, data, figure_name):
        """
        Gets DashaApp after calling layout and trace to construct figure in figure factory
        :param plot_meta_file_location (string) styling meta data file location in string format
        :param data (pandas dataframe) instrument data in a pandas dataframe
        :param figure_name (string) plot figure for reference in traces

        :return: DashApp (plotting.plot_factory.DashApp) DashApp object and attributes
        """

        data.set_index('Spectrum', inplace=True)
        layout = Layout(plot_meta_file_location, title=figure_name)
        trace_list = self.create_trace_list(data=data, layout=layout)
        figure = dict(data=trace_list, layout=layout.layout)

        return DashApp(figure=figure, app_id=figure_name)
