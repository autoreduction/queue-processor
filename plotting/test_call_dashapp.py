# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
A manual script to check dashapp is returned from factory
This script is acting as the plot handler
"""

from plotting.plot_factory.plot_factory import PlotFactory, Layout # Returns DashApp
from plotting.prepare_data import PrepareData  # Read CSV to generate dataframe


#  Get DataFrame
dataframe = PrepareData().prepare_data('multi_spectra_data_file.csv')  # csv file path

#  Get yaml file location as string
plot_meta_file_location = "plot_meta_language/plot_types/example.yaml"

dashapp = PlotFactory().create_plot(plot_meta_file_location=plot_meta_file_location,
                                    data=dataframe,
                                    figure_name="Instrument_Run_Number")
print(f"DashApp ID: {dashapp.app_id}")
# Run DashApp
if __name__ == '__main__':
    dashapp.app.run_server(debug=True)


