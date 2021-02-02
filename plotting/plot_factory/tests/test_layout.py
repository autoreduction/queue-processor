# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
""" Unit tests for plot factory Layout """

# Core Dependencies
import unittest
from unittest.mock import patch


# Internal Dependencies
from plotting.plot_factory.layout import Layout

# Mocked values
from plotting.plot_factory.tests.mocked_values import MockPlotVariables


class TestLayout(unittest.TestCase):

    @patch('plotting.plot_meta_language.interpreter.Interpreter.interpret')
    def test_read_plot_meta_data(self, mock_interpreter):
        """
        Test: read_plot_meta_data is called within Layout()
        When: Layout().extract_layout() is called with meta_file_location
        """
        mock_interpreter.return_value = MockPlotVariables().raw_interpreted_layout

        actual = Layout(MockPlotVariables().plot_meta_file_location,
                        'Instrument_Run_Number')._read_plot_meta_data()

        # assert that interpreter has been called with correct argument
        mock_interpreter.assert_called_with(MockPlotVariables().plot_meta_file_location)

        # return value assertions
        self.assertIsInstance(actual, dict)
        self.assertEqual(actual, MockPlotVariables().raw_interpreted_layout)

    @patch('plotting.plot_factory.plot_factory.Layout._read_plot_meta_data')
    def test_extract_layout(self, mock_rpmd):
        """
        Test: extract_layout is called within Layout() returning layout values in dictionary only
        When: mode and plot values exist in dict returned by read_plot_meta_data()
        """

        mock_rpmd.return_value = MockPlotVariables().raw_interpreted_layout

        actual = Layout(
            MockPlotVariables().raw_interpreted_layout,
            'Instrument_Run_Number')._extract_layout()

        self.assertIsInstance(actual, dict)
        self.assertEqual(actual, MockPlotVariables().processed_layout)
