# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for the ICAT monitor
"""

import unittest
import datetime
from mock import Mock, patch

import monitors.icat_monitor as icat_monitor
from monitors.settings import INSTRUMENTS


# pylint:disable=too-few-public-methods,unused-argument,missing-docstring
class DataFile(object):
    """
    Basic data file representation for testing
    """
    class Investigation(object):
        def __init__(self, name):
            self.name = name

    class DataSet(object):
        def __init__(self, investigation):
            self.investigation = investigation

    def __init__(self, df_name, rb_num):
        self.name = df_name
        self.investigation = self.Investigation(rb_num)
        self.dataset = self.DataSet(self.investigation)
        self.location = ""


# pylint:disable=missing-docstring
class TestICATMonitor(unittest.TestCase):
    """
    Test cases for the ICAT monitor
    """
    def test_get_run_number(self):
        """
        Test getting the run number from a file
        """
        run_num = icat_monitor.get_run_number('WISH00042587.nxs', 'WISH')
        self.assertEqual(run_num, '00042587')

    # pylint:disable=invalid-name
    def test_get_run_number_invalid_file(self):
        """
        Test handling of invalid file
        """
        run_num = icat_monitor.get_run_number('WISH_HELLO.RAW', 'WISH')
        self.assertEqual(run_num, None)

    def test_get_cycle_dates(self):
        """
        Test handling of cycle dates from ICAT
        """
        icat_client = Mock()
        icat_client.execute_query = Mock(return_value=[datetime.datetime(2018, 10, 18)])
        dates = icat_monitor.get_cycle_dates(icat_client)
        self.assertEqual(dates[0], '2018-10-18')
        self.assertEqual(dates[1], '2018-10-18')

    def test_get_cycle_dates_no_cycles(self):
        """
        Test handling of cycles when none are returned
        """
        icat_client = Mock()
        icat_client.execute_query = Mock(return_value=[])
        dates = icat_monitor.get_cycle_dates(icat_client)
        self.assertEqual(dates, None)

    def test_get_last_run_in_dates(self):
        """
        Test handling of run retrieval from ICAT
        """
        icat_client = Mock()
        inst_name = INSTRUMENTS[0]['name']
        file_name = inst_name + '3223.nxs'
        icat_client.execute_query = Mock(return_value=[DataFile(file_name, None)])
        run = icat_monitor.get_last_run_in_dates(icat_client,
                                                 inst_name,
                                                 ('2018-10-18', '2018-10-19'))
        self.assertEqual(run, '3223')

    # pylint:disable=invalid-name
    def test_get_last_run_in_dates_no_files(self):
        """
        Test handling of runs when no files are returned
        """
        icat_client = Mock()
        inst_name = INSTRUMENTS[0]['name']
        icat_client.execute_query = Mock(return_value=[])
        run = icat_monitor.get_last_run_in_dates(icat_client,
                                                 inst_name,
                                                 ('2018-10-18', '2018-10-19'))
        self.assertEqual(run, None)

    @patch('monitors.icat_monitor.get_cycle_dates', return_value='test')
    @patch('monitors.icat_monitor.get_last_run_in_dates', return_value=1234)
    def test_get_last_run(self, cycle_dates_mock, last_in_dates_mock):
        icat_client = Mock()
        actual = icat_monitor.get_last_run(icat_client, 'WISH')
        cycle_dates_mock.assert_called_once()
        last_in_dates_mock.assert_called_once()
        self.assertEqual(actual, 1234)

    @patch('monitors.icat_monitor.get_cycle_dates', return_value=None)
    def test_get_last_return_none_if_bad_date(self, cycle_dates_mock):
        icat_client = Mock()
        actual = icat_monitor.get_last_run(icat_client, 'WISH')
        cycle_dates_mock.assert_called_once()
        self.assertIsNone(actual)

    @patch('monitors.icat_monitor.get_cycle_dates', return_value='test')
    @patch('monitors.icat_monitor.get_last_run_in_dates', return_value=None)
    def test_get_last_no_runs_in_dates(self, mock_cycle_dates, mock_last_runs):
        icat_client = Mock()
        actual = icat_monitor.get_last_run(icat_client, 'WISH')
        mock_cycle_dates.assert_called_once()
        mock_last_runs.assert_called_once()
        self.assertIsNone(actual)

    def test_get_file_rb_and_location(self):
        df = DataFile('GEM1234.nxs', "1234")
        df.location = "/path/to/GEM1234.nxs"
        icat_client = Mock()
        icat_client.execute_query = Mock(return_value=[df])
        rb_num, loc = icat_monitor.get_file_rb_and_location(icat_client, "GEM", 1234)
        self.assertEqual(loc, "/path/to/GEM1234.nxs")
        self.assertEqual(rb_num, "1234")

    def test_get_file_rb_and_location_invalid(self):
        icat_client = Mock()
        icat_client.execute_query = Mock(return_value=None)
        rb_num, loc = icat_monitor.get_file_rb_and_location(icat_client, "GEM", 1234)
        self.assertIsNone(loc)
        self.assertIsNone(rb_num)

    # pylint:disable=no-self-use
    @patch('utils.clients.icat_client.ICATClient.__init__', return_value=None)
    @patch('utils.clients.icat_client.ICATClient.connect', return_value=None)
    def test_icat_login(self, mock_init, mock_connect):
        icat_monitor.icat_login()
        mock_init.assert_called_once()
        mock_connect.assert_called_once()
