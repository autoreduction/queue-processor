# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for plot factory DashApp
"""

# Core Dependencies
import unittest
from unittest.mock import patch, Mock

# Internal Dependencies
from plotting.plot_factory.dashapp import DashApp

# Mocked values
from plotting.plot_factory.tests.mocked_values import MockPlotVariables


class TestDashApp(unittest.TestCase):

    def setUp(self):
        """Contains setup variables to be used in unit tests for Trace class methods"""
        self.figure = None

    @patch("plotting.plot_factory.dashapp.DjangoDash")
    def test_create_dashapp(self, mock_dashapp):
        """
        Test:create_dashapp() is called returning an instance of DashApp object
        When: called with figure and app_id by DashApp()
        """
        mock_dash_obj = Mock()
        mock_dashapp.return_value = mock_dash_obj
        # Assert a DashApp is returned
        DashApp(self.figure, MockPlotVariables().plot_name)
        mock_dashapp.assert_called_once()

        # self.assertEqual(mock_dash_obj, "Div([Div(Graph(id='Instrument_Run_number'))])")
        self.assertEqual('Div', type(mock_dash_obj.layout).__name__)
        self.assertEqual("[Div(Graph(id='Instrument_Run_number'))]",
                         str(mock_dash_obj.layout.__dict__['children']))


