
import unittest
import datetime
from mock import Mock

import monitors.icat_monitor as icat_monitor
import monitors.settings


# pylint:disable=too-few-public-methods
class DataFile(object):
    """
    Basic data file representation for testing
    """
    def __init__(self, df_name):
        self.name = df_name


class TestICATMonitor(unittest.TestCase):
    def test_get_run_number(self):
        run_num = icat_monitor.get_run_number('WISH00042587.nxs', 'WISH')
        self.assertEqual(run_num, '00042587')

    def test_get_cycle_dates(self):
        icat_client = Mock()
        icat_client.execute_query = Mock(return_value=[datetime.datetime(2018, 10, 18)])
        dates = icat_monitor.get_cycle_dates(icat_client)
        self.assertEqual(dates[0], '2018-10-18')
        self.assertEqual(dates[1], '2018-10-18')

    def test_get_instrument_run(self):
        icat_client = Mock()
        icat_client.execute_query = Mock(return_value=[DataFile("GEM3223.nxs")])
        run = icat_monitor.get_instrument_run(icat_client, 'GEM', ('2018-10-18', '2018-10-19'))
        self.assertEqual(run, '3223')