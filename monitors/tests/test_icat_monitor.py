"""
Unit tests for the ICAT monitor
"""

import unittest
import datetime
from mock import Mock

import monitors.icat_monitor as icat_monitor
from monitors.settings import INSTRUMENTS


# pylint:disable=too-few-public-methods,unused-argument
class DataFile(object):
    """
    Basic data file representation for testing
    """
    def __init__(self, df_name):
        self.name = df_name


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
        icat_client.execute_query = Mock(return_value=[DataFile(file_name)])
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
