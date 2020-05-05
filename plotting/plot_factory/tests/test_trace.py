# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for plot factory Trace
"""

# Core Dependencies
import unittest

import plotly

# Mocked values
from plotting.plot_factory.tests.mocked_values import MockPlotVariables


class TestTrace(unittest.TestCase):

    def setUp(self):
        """Contains setup variables to be used in unit tests for Trace class methods"""

        self.error_bars = True

    def test_trace_dict_error_bars_set_true(self):
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
        actual = MockPlotVariables().trace_object.trace_dict(
            MockPlotVariables().indexed_multi_single_raw_data_dataframe, False)

        self.assertIsInstance(actual, dict)
        self.assertEqual(actual, MockPlotVariables().trace_multi_single_error_y_not_visible)

    def test_dict_to_string(self):
        """
        Test: dict_to_string() is returned as string in expected format
        When: called with dictionary by create_trace()
        """

        actual = MockPlotVariables().trace_object.dict_to_string(
            MockPlotVariables().trace_multi_single_to_string)

        self.assertIsInstance(actual, str)

    def test_create_trace(self):
        """
        Test: _create_connection() is called within connect()
        When: client._connection is None
        """

        actual = MockPlotVariables().trace_object.trace

        self.assertIsInstance(actual, plotly.graph_objs.Scattergl)