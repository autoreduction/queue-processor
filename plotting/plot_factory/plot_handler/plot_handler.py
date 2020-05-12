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
import dash_core_components as dcc
import dash_html_components as html

from plotting.plot_factory.plot_factory import PlotFactory, Layout  # Returns DashApp
from plotting.prepare_data import PrepareData  # Read CSV to generate dataframe

#  Get DataFrame -
dataframe = PrepareData().prepare_data('../../plotting/multi_spectra_data_file.csv')  # csv path

#  Get .yaml file location as string
plot_meta_file_location = "../../plotting/plot_meta_language/plot_types/example.yaml"

# Dashapp
dashapp = PlotFactory().create_plot(plot_meta_file_location=plot_meta_file_location,
                                       data=dataframe,
                                       figure_name="Instrument_Run_Number")