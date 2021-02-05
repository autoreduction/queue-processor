# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Location of mocked hard coded values for plot_factory unit tests
"""

import pandas as pd

# Internal Dependencies
from plotting.plot_factory.trace import Trace


class MockPlotVariables:
    """Class containing mock variables for use in plot factory unit tests"""
    def __init__(self):
        """Hard coded variables for use in plot factory unit tests"""

        # Plot configuration values
        self.plot_meta_file_location = "relative_location/to/file"
        self.plot_type = 'Scattergl'
        self.plot_name = "Instrument_Run_number"
        self.plot_mode = 'lines'

        # Raw dictionaries with single-multi and multi-single trace
        self.multi_single_trace_raw_data_dictionary = {
            'Spectrum': [1, 1],
            'X': [100.25, 100.75],
            'Y': [8210, 6837],
            'E': [90.6091, 82.6862]
        }
        self.single_multi_trace_raw_data_dictionary = {
            'Spectrum': [1, 2],
            'X': [100.25, 100.75],
            'Y': [8210, 6837],
            'E': [90.6091, 82.6862]
        }

        # Raw dataframe single-multi and multi-single trace
        self.raw_multi_single_data_dataframe = pd.DataFrame(self.multi_single_trace_raw_data_dictionary)
        self.raw_single_multi__data_dataframe = pd.DataFrame(self.single_multi_trace_raw_data_dictionary)

        # Indexed dataframe single-multi and multi-single trace
        self.indexed_multi_single_raw_data_dataframe = \
            self.raw_multi_single_data_dataframe.set_index('Spectrum')
        self.indexed_single_multi_raw_data_dataframe = \
            self.raw_single_multi__data_dataframe.set_index('Spectrum')

        # Layout pre and post processing
        self.raw_interpreted_layout = {
            'xaxis': {
                'type': 'log',
                'title': 'x_axis',
                'unit': 'unit'
            },
            'title': 'Instrument_Run_Number',
            'yaxis': {
                'type': 'log',
                'title': 'y_axis',
                'unit': 'unit'
            }
        }

        self.processed_layout = {
            'xaxis': {
                'type': 'log',
                'title': 'x_axis',
                'unit': 'unit'
            },
            'title': 'Instrument_Run_Number',
            'yaxis': {
                'type': 'log',
                'title': 'y_axis',
                'unit': 'unit'
            }
        }

        # Trace object using hard coded values
        self.trace_object = Trace(data=self.indexed_multi_single_raw_data_dataframe,
                                  plot_style=self.plot_type,
                                  plot_name=self.plot_name,
                                  mode=self.plot_mode,
                                  error_bars=True)

        # trace dictionary structure for multi-single trace
        self.trace_multi_single = {
            'x': self.indexed_multi_single_raw_data_dataframe['X'],
            'y': self.indexed_multi_single_raw_data_dataframe['Y'],
            'error_y': {
                'type': 'data',
                'array': self.indexed_multi_single_raw_data_dataframe['E'].to_list(),
                'visible': True
            }
        }

        self.trace_multi_single_error_y_not_visible = {
            'x': self.indexed_multi_single_raw_data_dataframe['X'],
            'y': self.indexed_multi_single_raw_data_dataframe['Y'],
            'error_y': {
                'type': 'data',
                'array': self.indexed_multi_single_raw_data_dataframe['E'].to_list(),
                'visible': False
            }
        }

        self.trace_multi_single_to_string = {
            'x': self.indexed_multi_single_raw_data_dataframe['X'],
            'y': self.indexed_multi_single_raw_data_dataframe['Y'],
            'error_y': {
                'type': 'data',
                'array': self.indexed_multi_single_raw_data_dataframe['E'].to_list(),
                'visible': True
            },
            'name': self.plot_name
        }
