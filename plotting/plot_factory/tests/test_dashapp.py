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

import dash

# Internal Dependencies
from plotting.plot_factory.dashapp import DashApp

# Mocked values
from plotting.plot_factory.tests.mocked_values import MockPlotVariables


class TestDashApp(unittest.TestCase):

    def setUp(self):
        """Contains setup variables to be used in unit tests for Trace class methods"""
        self.figure = None

    def test_create_dashapp(self):
        """
        Test:create_dashapp() is called returning an instance of DashApp object
        When: called with figure and app_id by DashApp()
        """
        # Assert a DashApp is returned
        actual = DashApp(self.figure, MockPlotVariables().plot_name).create_dashapp()

        self.assertIsInstance(actual, dash.dash.Dash)

