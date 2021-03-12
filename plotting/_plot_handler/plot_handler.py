# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Template Script to display how Plot Handler can create DashApps

- Note file paths are relative to WebApp/autoreduce_webapp/autoreduce_webapp/urls.py (hence ../../)
"""

from plotting.plot_factory.plot_factory import PlotFactory  # Returns DashApp
from plotting.prepare_data import PrepareData  # Read CSV to generate dataframe


class DjangoDashApp:
    """Returns a Dash"""
    def __init__(self, data_location, meta_location, dashapp_name):
        self.data_location = data_location  # From repository root
        self.meta_location = meta_location  # From repository root
        self.dashapp_name = dashapp_name
        self.dashapp = self.get_dashapp()

    def get_dashapp(self):
        """Get DashApp from Plot Factory"""
        return PlotFactory().create_plot(plot_meta_file_location=f"../../{self.meta_location}",
                                         data=PrepareData().prepare_data(f"../../{self.data_location}"),
                                         figure_name=self.dashapp_name)
