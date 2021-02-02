# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
""" Unit tests for plot factory """

# Core Dependencies
import unittest
from unittest.mock import patch, PropertyMock

# Internal Dependencies
from plotting.plot_factory.plot_factory import PlotFactory

# Mocked values
from plotting.plot_factory.tests.mocked_values import MockPlotVariables


class TestPlotFactory(unittest.TestCase):

    @patch('plotting.plot_factory.plot_factory.Trace')
    @patch('plotting.plot_factory.plot_factory.Layout')
    def test_get_trace_list(self, mock_layout, _):
        """
        Test: create_trace_list is called within TestPlotFactory().create_plot()
        When: trace_list = []
        """
        mock_layout.return_value.mode = PropertyMock("mock_mode")
        mock_layout.return_value.plot_type = PropertyMock("mock_plot_type")
        layout = mock_layout

        # Assert that a list of trace object is returned
        actual = PlotFactory().create_trace_list(
            MockPlotVariables().indexed_single_multi_raw_data_dataframe,
            layout)
        self.assertIsInstance(actual, list)  # is list
        self.assertEqual(len(actual), 2)

    @patch("plotting.plot_factory.dashapp.DjangoDash")
    @patch('plotting.plot_factory.plot_factory.PlotFactory.create_trace_list')
    @patch('plotting.plot_factory.plot_factory.Layout')
    def test_construct_plot(self, mock_layout, mock_get_trace,  mock_dashapp):
        """
        Test: dashapp object is returned
        When: called with self.create_trace_list() and Layout().layout
        """
        actual = PlotFactory().create_plot(
            plot_meta_file_location=MockPlotVariables().plot_meta_file_location,
            data=MockPlotVariables().raw_multi_single_data_dataframe,
            figure_name=MockPlotVariables().plot_name)

        mock_dashapp.assert_called_once()

        self.assertEqual('Instrument_Run_number', actual.app_id)
