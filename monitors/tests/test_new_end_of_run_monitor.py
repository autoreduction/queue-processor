"""
Unit tests for the end of run monitor
"""
import unittest
import os
import json
import csv
from mock import (Mock, patch, call)

from utils.clients.queue_client import QueueClient
from monitors.settings import (CYCLE_FOLDER, LAST_RUNS_CSV)
from monitors.new_end_of_run_monitor import (InstrumentMonitor,
                                             get_prefix_zeros,
                                             FileNotFoundError,
                                             update_last_runs,
                                             main)

# Test data
SUMMARY_FILE = ("WIS44731Hayden,Waite,"
                "CanfielCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 09:14:23    34.3 1820461\n"
                "WIS44732Hayden,Waite,"
                "CanfielCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 10:23:47    40.0 1820461\n"
                "WIS44733Hayden,Waite,"
                "CanfielCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 11:34:25     9.0 1820461\n")
LAST_RUN_FILE = "WISH 00044733 0 \n"
RUN_DICT = {'instrument': 'WISH',
            'run_number': '00044733',
            'data': '/my/data/dir/cycle_18_4/WISH00044733.nxs',
            'rb_number': '1820461',
            'facility': 'ISIS'}
CSV_FILE = "WISH,44733,lastrun_wish.txt,summary_wish.txt,data_dir,.nxs"


# pylint:disable=missing-docstring,no-self-use
class TestEndOfRunMonitor(unittest.TestCase):
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

    # pylint:disable=invalid-name
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
        self.assertEqual(RUN_DICT, data_dict)

    @patch('os.path.isfile', return_value=True)
    def test_submit_run(self, isfile_mock):
        client = Mock()
        client.send = Mock(return_value=None)
        client.serialise_data = Mock(return_value=RUN_DICT)

        inst_mon = InstrumentMonitor(client, 'WISH')
        inst_mon.data_dir = '/my/data/dir'
        data_loc = os.path.join(inst_mon.data_dir, CYCLE_FOLDER, 'WISH00044733.nxs')
        inst_mon.submit_run('1820461', '00044733', 'WISH00044733.nxs')
        client.send.assert_called_with('/queue/DataReady', json.dumps(RUN_DICT), priority='9')
        isfile_mock.assert_called_with(data_loc)

    @patch('os.path.isfile', return_value=False)
    def test_submit_run_file_not_found(self, isfile_mock):
        client = Mock()
        client.send = Mock(return_value=None)
        client.serialise_data = Mock(return_value=RUN_DICT)

        inst_mon = InstrumentMonitor(client, 'WISH')
        inst_mon.data_dir = '/my/data/dir'
        data_loc = os.path.join(inst_mon.data_dir, CYCLE_FOLDER, 'WISH00044733.nxs')
        with self.assertRaises(FileNotFoundError):
            inst_mon.submit_run('1820461', '00044733', 'WISH00044733.nxs')
        isfile_mock.assert_called_with(data_loc)

    def test_submit_run_difference(self):
        # Setup test
        inst_mon = InstrumentMonitor(None, 'WISH')
        inst_mon.submit_run = Mock(return_value=None)
        inst_mon.file_ext = '.nxs'
        inst_mon.read_instrument_last_run = Mock(return_value=['WISH',
                                                               '00044733',
                                                               '0'])
        inst_mon.read_rb_number_from_summary = Mock(return_value='1820461')

        # Perform test
        inst_mon.submit_run_difference(44731)
        inst_mon.submit_run.assert_has_calls([call('1820461', '00044732', 'WISH00044732.nxs'),
                                              call('1820461', '00044733', 'WISH00044733.nxs')])

    @patch('monitors.new_end_of_run_monitor.InstrumentMonitor.__init__',
           return_value=None)
    @patch('monitors.new_end_of_run_monitor.InstrumentMonitor.submit_run_difference',
           return_value='44736')
    def test_update_last_runs(self, run_diff_mock, inst_mon_mock):
        # Setup test
        with open('test_last_runs.csv', 'w') as last_runs_fp:
            last_runs_fp.write(CSV_FILE)

        # Perform test
        update_last_runs('test_last_runs.csv')
        inst_mon_mock.assert_called()
        run_diff_mock.assert_called_with('44733')

        # Read the CSV and ensure it has been updated
        with open('test_last_runs.csv') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                self.assertEqual('44736', row[1])
        os.remove('test_last_runs.csv')

    @patch('monitors.new_end_of_run_monitor.update_last_runs')
    def test_main(self, update_last_runs_mock):
        main()
        update_last_runs_mock.assert_called_with(LAST_RUNS_CSV)
        update_last_runs_mock.assert_called_once()
