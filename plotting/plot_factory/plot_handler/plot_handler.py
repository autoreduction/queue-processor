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

from plotting.plot_factory.plot_factory import PlotFactory, Layout  # Returns DashApp
from plotting.prepare_data import PrepareData  # Read CSV to generate dataframe

# Convert raw data to Pandas Dataframe
dataframe = PrepareData().prepare_data('../../.csv_location')

# Get .yaml file location
plot_meta_file_location = "../../<.yaml_location>"

# DjangoDash Dashapp Object
dashapp = PlotFactory().create_plot(plot_meta_file_location=plot_meta_file_location,
                                    data=dataframe,
                                    figure_name="Instrument_Run_Number")
