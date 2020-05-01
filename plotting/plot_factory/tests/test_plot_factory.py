# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for plot factory
"""

# TODO Tests to cover: unable to find plot meta data;
#  unable to interpret dataframe;
#  unable to find spectrum
#  - Add hard coded string equivalent of dictionary to test_dict_to_string
#  - Add Error bars to yaml file options

import unittest
from mock import patch, Mock, PropertyMock

import pandas as pd
import plotly
import dash

# Internal Dependencies
from plotting.plot_factory.plot_factory import PlotFactory, Layout, Trace, DashApp

# Mocked values
from plotting.plot_factory.tests.mocked_values import MockPlotVariables


class TestPlotFactory(unittest.TestCase):

    def setUp(self):
        """
        Contains mocked objects to pass into plot factory class methods.

        Test: get_trace_list is called within TestPlotFactory().construct_plot()
        When: trace_list = []
        """

    @patch('plotting.plot_factory.plot_factory.Trace')
    @patch('plotting.plot_factory.plot_factory.Layout')
    def test_get_trace_list(self, mock_layout, _):
        """
        Test: get_trace_list is called within TestPlotFactory().construct_plot()
        When: trace_list = []
        """
        mock_layout.return_value.mode = PropertyMock("mock_mode")
        mock_layout.return_value.plot_type = PropertyMock("mock_plot_type")
        layout = mock_layout

        # Assert that a list of trace object is returned
        actual = PlotFactory().get_trace_list(
            MockPlotVariables().indexed_single_multi_raw_data_dataframe,
            layout, MockPlotVariables().plot_name)
        self.assertIsInstance(actual, list)  # is list
        self.assertEqual(len(actual), 2)

    # @patch('plotting.plot_factory.plot_factory.DashApp')
    @patch('plotting.plot_factory.plot_factory.PlotFactory.get_trace_list')
    @patch('plotting.plot_factory.plot_factory.Layout')
    def test_construct_plot(self, mock_layout, mock_get_trace):
        """
        Test: dashapp object is returned
        When: called with self.get_trace_list() and Layout().layout
        """
        actual = PlotFactory().construct_plot(
            plot_meta_file_location=MockPlotVariables().plot_meta_file_location,
            data=MockPlotVariables().raw_multi_single_data_dataframe,
            figure_name=MockPlotVariables().plot_name)

        self.assertIsInstance(actual.app, dash.dash.Dash)


class TestLayout(unittest.TestCase):

    @patch('plotting.plot_meta_language.interpreter.Interpreter.interpret')
    def test_read_plot_meta_data(self, mock_interpreter):
        """
        Test: read_plot_meta_data is called within Layout()
        When: Layout().extract_layout() is called with meta_file_location
        """
        mock_interpreter.return_value = MockPlotVariables().raw_interpreted_layout

        actual = Layout(MockPlotVariables().plot_meta_file_location).read_plot_meta_data()

        # assert that interpreter has been called with correct argument
        mock_interpreter.assert_called_with(MockPlotVariables().plot_meta_file_location)

        # return value assertions
        self.assertIsInstance(actual, dict)
        self.assertEqual(actual, MockPlotVariables().raw_interpreted_layout)

    @patch('plotting.plot_factory.plot_factory.Layout.read_plot_meta_data')
    def test_extract_layout(self, mock_rpmd):
        """
        Test: extract_layout is called within Layout() returning layout values in dictionary only
        When: mode and plot values exist in dict returned by read_plot_meta_data()
        """

        mock_rpmd.return_value = MockPlotVariables().raw_interpreted_layout

        actual = Layout(
            MockPlotVariables().raw_interpreted_layout).extract_layout(
            MockPlotVariables().raw_interpreted_layout)

        self.assertIsInstance(actual, dict)
        self.assertEqual(actual, MockPlotVariables().processed_layout)


class TestTrace(unittest.TestCase):

    def setUp(self):
        """Contains setup variables to be used in unit tests for Trace class methods"""

        self.plot_style = 'Scattergl'
        self.plot_name = "Instrument_Run_number"
        self.mode = 'lines'
        self.error_bars = True

        self.data = pd.DataFrame({'Spectrum': [1, 1],
                                  'X': [100.25, 100.75],
                                  'Y': [8210, 6837],
                                  'E': [90.6091, 82.6862]})
        self.dataframe = self.data.set_index('Spectrum')

        self.trace_no_error_bars = {
            'x': "data['X']",
            'y': "data['Y']"}

        self.trace_to_string = {'x': "data['X']",
                                'y': "data['Y']",
                                'error_y': {
                                    'type': 'data',
                                    'array': self.dataframe['E'].to_list(),
                                    'visible': True},
                                'name': self.plot_name
                                }

        self.trace_as_string = None

    def test_trace_dict__error_bars_set_true(self):
        """
        Test: trace_dict() returns a dict in expected trace format containing error_bars
        When: called with dataframe and error_bars=True
        """

        actual = MockPlotVariables().trace_object.trace_dict(
            data=MockPlotVariables().indexed_multi_single_raw_data_dataframe,
            error_bars=self.error_bars)

        self.assertIsInstance(actual, dict)
        self.assertEqual(actual, MockPlotVariables().trace_multi_single)

    def test_trace_dict__error_bars_set_false(self):
        """
        Test: trace_dict() returns a dict in expected trace format without error_bars
        When: called with dataframe and error_bars=False
        """
        actual = MockPlotVariables().trace_object.trace_dict(self.dataframe, False)

        self.assertIsInstance(actual, dict)
        self.assertEqual(actual, self.trace_no_error_bars)

    def test_dict_to_string(self):
        """
        Test: dict_to_string() is returned as string in expected format
        When: called with dictionary by create_trace()
        """

        actual = MockPlotVariables().trace_object.dict_to_string(self.trace_to_string)
        self.assertIsInstance(actual, str)

    def test_create_trace(self):
        """
        Test: _create_connection() is called within connect()
        When: client._connection is None
        """

        actual = MockPlotVariables().trace_object.trace

        self.assertIsInstance(actual, plotly.graph_objs.Scattergl)


class TestDashApp(unittest.TestCase):

    def setUp(self):
        """Contains setup variables to be used in unit tests for Trace class methods"""
        self.figure = None
        self.app_id = "Instrument_Run_number"

    def test_create_dashapp(self):
        """
        Test:create_dashapp() is called returning an instance of DashApp object
        When: called with figure and app_id by DashApp()
        """
        # Assert a DashApp is returned
        actual = DashApp(self.figure, self.app_id).create_dashapp()

        self.assertIsInstance(actual, dash.dash.Dash)
        # ToDO: Assert with a hard coded figure

