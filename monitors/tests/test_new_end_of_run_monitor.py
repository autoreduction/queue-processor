import unittest
import os

from utils.clients.queue_client import QueueClient
from monitors.new_end_of_run_monitor import (InstrumentMonitor, get_prefix_zeros)

# Test data
SUMMARY_FILE = ("WIS44731Hayden,Waite,CanfielCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 09:14:23    34.3 1820461\n"
                "WIS44732Hayden,Waite,CanfielCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 10:23:47    40.0 1820461\n"
                "WIS44733Hayden,Waite,CanfielCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 11:34:25     9.0 1820461\n")
LAST_RUN_FILE = "WISH 00044733 0 \n"


class TestEndOfRunMonitor(unittest.TestCase):
    """
    Test the end of run monitor
    """
    def test_get_prefix_zeros(self):
        run_number = '00012345'
        zeros = get_prefix_zeros(run_number)
        self.assertEqual('000', zeros)

    def test_get_prefix_zeros_no_zeros(self):
        run_number = '12345'
        zeros = get_prefix_zeros(run_number)
        self.assertEqual('', zeros)

    def test_read_instrument_last_run(self):
        with open('test_lastrun.txt', 'w') as last_run_fp:
            last_run_fp.write(LAST_RUN_FILE)

        inst_mon = InstrumentMonitor(None, 'WISH')
        inst_mon.last_run_file = 'test_lastrun.txt'
        last_run_data = inst_mon.read_instrument_last_run()

        self.assertEqual('WISH', last_run_data[0])
        self.assertEqual('00044733', last_run_data[1])
        self.assertEqual('0', last_run_data[2])
        os.remove('test_lastrun.txt')

    def test_read_rb_number_from_summary(self):
        with open('test_summary.txt', 'w') as summary_fp:
            summary_fp.write(SUMMARY_FILE)

        inst_mon = InstrumentMonitor(None, 'WISH')
        inst_mon.summary_file = 'test_summary.txt'
        rb_number = inst_mon.read_rb_number_from_summary(44733)
        self.assertEqual('1820461', rb_number)
        os.remove('test_summary.txt')

    def test_build_dict(self):
        client = QueueClient()
        inst_mon = InstrumentMonitor(client, 'WISH')
        data_loc = '/my/data/dir/cycle_18_4/WISH00044733.nxs'
        rb_number = '1820461'
        run_number = '00044733'
        data_dict = inst_mon.build_dict(rb_number, run_number, data_loc)
        expected = {'instrument': 'WISH',
                    'run_number': run_number,
                    'data': data_loc,
                    'rb_number': rb_number,
                    'facility': 'ISIS'}
        self.assertEqual(expected, data_dict)
