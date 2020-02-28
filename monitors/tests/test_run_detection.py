"""
Unit tests for the end of run monitor
"""
import unittest
import os
import json
import csv
from filelock import FileLock
from mock import (Mock, patch, call)

from utils.clients.queue_client import QueueClient
from monitors.settings import (CYCLE_FOLDER, LAST_RUNS_CSV)
import monitors.run_detection as eorm
from monitors.run_detection import (InstrumentMonitor,
                                    InstrumentMonitorError)

# Test data
SUMMARY_FILE = ("WIS44731Smith,Smith,"
                "SmithCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 09:14:23    34.3 1820461\n"
                "WIS44732Smith,Smith,"
                "SmithCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 10:23:47    40.0 1820461\n"
                "WIS44733Smith,Smith,"
                "SmithCeAuSb2 MRSX ROT=15.05 s28-MAR-2019 11:34:25     9.0 1820461\n")
LAST_RUN_FILE = "WISH 00044733 0 \n"
INVALID_LAST_RUN_FILE = "INVALID LAST RUN FILE"
RUN_DICT = {'instrument': 'WISH',
            'run_number': '00044733',
            'data': '/my/data/dir/cycle_18_4/WISH00044733.nxs',
            'rb_number': '1820461',
            'facility': 'ISIS',
            'started_by': 0}
RUN_DICT_SUMMARY = {'instrument': 'WISH',
                    'run_number': '00044733',
                    'data': '/my/data/dir/cycle_18_4/WISH00044733.nxs',
                    'rb_number': '1820333',
                    'facility': 'ISIS'}
CSV_FILE = "WISH,44733,lastrun_wish.txt,summary_wish.txt,data_dir,.nxs"


# pylint:disable=too-few-public-methods,missing-function-docstring
class DataHolder:
    """
    Small helper class to represent expected nexus data format
    """

    def __init__(self, data):
        self.data = data

    def get(self, _):
        mock_value = Mock()
        mock_value.value = self.data
        return mock_value


# nexusformat mock objects
NXLOAD_MOCK = Mock()
NXLOAD_MOCK.items = Mock(return_value=[('raw_data_1', DataHolder([b'1910232']))])

NXLOAD_MOCK_EMPTY = Mock()
NXLOAD_MOCK_EMPTY.items = Mock(return_value=[('raw_data_1', DataHolder(['']))])


# pylint:disable=missing-docstring,no-self-use,too-many-public-methods
class TestRunDetection(unittest.TestCase):
    def tearDown(self):
        if os.path.isfile('test_lastrun.txt'):
            os.remove('test_lastrun.txt')
        if os.path.isfile('test_summary.txt'):
            os.remove('test_summary.txt')
        if os.path.isfile('test_last_runs.csv'):
            os.remove('test_last_runs.csv')

    def test_get_prefix_zeros(self):
        run_number = '00012345'
        zeros = eorm.get_prefix_zeros(run_number)
        self.assertEqual('000', zeros)

    def test_get_prefix_zeros_no_zeros(self):
        run_number = '12345'
        zeros = eorm.get_prefix_zeros(run_number)
        self.assertEqual('', zeros)

    def test_get_prefix_zeros_all_zeros(self):
        run_number = '00000'
        zeros = eorm.get_prefix_zeros(run_number)
        self.assertEqual(run_number, zeros)

    def test_read_instrument_last_run(self):
        with open('test_lastrun.txt', 'w') as last_run:
            last_run.write(LAST_RUN_FILE)

        inst_mon = InstrumentMonitor(None, 'WISH')
        inst_mon.last_run_file = 'test_lastrun.txt'
        last_run_data = inst_mon.read_instrument_last_run()

        self.assertEqual('WISH', last_run_data[0])
        self.assertEqual('00044733', last_run_data[1])
        self.assertEqual('0', last_run_data[2])

    # pylint:disable=invalid-name
    def test_read_instrument_last_run_invalid_length(self):
        with open('test_lastrun.txt', 'w') as last_run:
            last_run.write(INVALID_LAST_RUN_FILE)

        inst_mon = InstrumentMonitor(None, 'WISH')
        inst_mon.last_run_file = 'test_lastrun.txt'
        with self.assertRaises(InstrumentMonitorError):
            inst_mon.read_instrument_last_run()

    # pylint:disable=invalid-name
    def test_read_rb_number_from_summary(self):
        with open('test_summary.txt', 'w') as summary:
            summary.write(SUMMARY_FILE)

        inst_mon = InstrumentMonitor(None, 'WISH')
        inst_mon.summary_file = 'test_summary.txt'
        rb_number = inst_mon.read_rb_number_from_summary()
        self.assertEqual('1820461', rb_number)

    def test_read_rb_number_from_summary_invalid(self):
        with open('test_summary.txt', 'w') as summary:
            summary.write(' ')
        inst_mon = InstrumentMonitor(None, 'WISH')
        inst_mon.summary_file = 'test_summary.txt'
        self.assertRaises(InstrumentMonitorError, inst_mon.read_rb_number_from_summary)

    def test_build_dict(self):
        client = QueueClient()
        inst_mon = InstrumentMonitor(client, 'WISH')
        data_loc = '/my/data/dir/cycle_18_4/WISH00044733.nxs'
        rb_number = '1820461'
        run_number = '00044733'
        data_dict = inst_mon.build_dict(rb_number, run_number, data_loc)
        self.assertEqual(RUN_DICT, data_dict)

    @patch('os.path.isfile', return_value=True)
    @patch('monitors.run_detection.read_rb_number_from_nexus_file',
           return_value='1820461')
    def test_submit_run(self, read_rb_mock, isfile_mock):
        client = Mock()
        client.send = Mock(return_value=None)
        client.serialise_data = Mock(return_value=RUN_DICT)

        inst_mon = InstrumentMonitor(client, 'WISH')
        inst_mon.data_dir = '/my/data/dir'
        data_loc = os.path.join(inst_mon.data_dir, CYCLE_FOLDER, 'WISH00044733.nxs')

        inst_mon.submit_run('1820333', '00044733', 'WISH00044733.nxs')
        client.send.assert_called_with('/queue/DataReady', json.dumps(RUN_DICT), priority='9')
        isfile_mock.assert_called_with(data_loc)
        read_rb_mock.assert_called_once_with(data_loc)

    @patch('os.path.isfile', return_value=False)
    def test_submit_run_file_not_found(self, isfile_mock):
        client = Mock()
        client.send = Mock(return_value=None)
        client.serialise_data = Mock(return_value=RUN_DICT)

        inst_mon = InstrumentMonitor(client, 'WISH')
        inst_mon.data_dir = '/my/data/dir'
        data_loc = os.path.join(inst_mon.data_dir, CYCLE_FOLDER, 'WISH00044733.nxs')
        with self.assertRaises(FileNotFoundError):
            inst_mon.submit_run('1820333', '00044733', 'WISH00044733.nxs')
        isfile_mock.assert_called_with(data_loc)

    @patch('os.path.isfile', return_vaule=True)
    @patch('monitors.run_detection.read_rb_number_from_nexus_file',
           return_value=None)
    def test_submit_run_invalid_nexus(self, read_rb_mock, isfile_mock):
        client = Mock()
        client.send = Mock(return_value=None)
        client.serialise_data = Mock(return_value=RUN_DICT_SUMMARY)

        inst_mon = InstrumentMonitor(client, 'WISH')
        inst_mon.data_dir = '/my/data/dir'
        data_loc = os.path.join(inst_mon.data_dir, CYCLE_FOLDER, 'WISH00044733.nxs')

        inst_mon.submit_run('1820333', '00044733', 'WISH00044733.nxs')
        client.send.assert_called_with('/queue/DataReady',
                                       json.dumps(RUN_DICT_SUMMARY),
                                       priority='9')
        isfile_mock.assert_called_with(data_loc)
        read_rb_mock.assert_called_once_with(data_loc)

    @patch('monitors.run_detection.h5py.File', return_value=NXLOAD_MOCK)
    def test_read_rb_number_from_nexus(self, nxload_mock):
        rb_num = eorm.read_rb_number_from_nexus_file('mynexus.nxs')
        self.assertEqual(rb_num, '1910232')
        kwargs = {"mode": "r"}
        nxload_mock.assert_called_once_with('mynexus.nxs', **kwargs)

    @patch('monitors.run_detection.h5py.File', return_value=NXLOAD_MOCK_EMPTY)
    def test_read_rb_number_from_nexus_invalid(self, nxload_mock):
        rb_num = eorm.read_rb_number_from_nexus_file('mynexus.nxs')
        self.assertIsNone(rb_num)
        kwargs = {"mode": "r"}
        nxload_mock.assert_called_once_with('mynexus.nxs', **kwargs)

    @patch('monitors.run_detection.h5py.File', side_effect=IOError('HDF4 file'))
    def test_read_rb_number_from_nexus_hdf4(self, nxload_mock):
        rb_num = eorm.read_rb_number_from_nexus_file('mynexus.nxs')
        self.assertIsNone(rb_num)
        kwargs = {"mode": "r"}
        nxload_mock.assert_called_once_with('mynexus.nxs', **kwargs)

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
        run_number = inst_mon.submit_run_difference(44731)
        self.assertEqual(run_number, '44733')
        inst_mon.submit_run.assert_has_calls([call('1820461', '00044732', 'WISH00044732.nxs'),
                                              call('1820461', '00044733', 'WISH00044733.nxs')])

    def test_submit_run_difference_no_file(self):
        # Setup test
        inst_mon = InstrumentMonitor(None, 'WISH')
        inst_mon.submit_run = Mock(side_effect=FileNotFoundError('File not found'))
        inst_mon.file_ext = '.nxs'
        inst_mon.read_instrument_last_run = Mock(return_value=['WISH',
                                                               '00044733',
                                                               '0'])
        inst_mon.read_rb_number_from_summary = Mock(return_value='1820461')

        # Perform test
        run_number = inst_mon.submit_run_difference(44731)
        self.assertEqual(run_number, '44731')

    @patch('monitors.run_detection.InstrumentMonitor.__init__',
           return_value=None)
    @patch('monitors.run_detection.InstrumentMonitor.submit_run_difference',
           return_value='44736')
    def test_update_last_runs(self, run_diff_mock, inst_mon_mock):
        # Setup test
        with open('test_last_runs.csv', 'w') as last_runs:
            last_runs.write(CSV_FILE)

        # Perform test
        eorm.update_last_runs('test_last_runs.csv')
        inst_mon_mock.assert_called()
        run_diff_mock.assert_called_with('44733')

        # Read the CSV and ensure it has been updated
        with open('test_last_runs.csv') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                if row:  # Avoid the empty rows
                    self.assertEqual('44736', row[1])

    @patch('monitors.run_detection.InstrumentMonitor.__init__',
           return_value=None)
    @patch('monitors.run_detection.InstrumentMonitor.submit_run_difference',
           side_effect=InstrumentMonitorError('Error'))
    def test_update_last_runs_with_error(self, run_diff_mock, inst_mon_mock):
        # Setup test
        with open('test_last_runs.csv', 'w') as last_runs:
            last_runs.write(CSV_FILE)

        # Perform test
        eorm.update_last_runs('test_last_runs.csv')
        inst_mon_mock.assert_called()
        run_diff_mock.assert_called_with('44733')

        # Read the CSV and ensure it has been updated
        with open('test_last_runs.csv') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                if row:  # Avoid the empty rows
                    self.assertEqual('44733', row[1])

    @patch('monitors.run_detection.update_last_runs')
    def test_main(self, update_last_runs_mock):
        eorm.main()
        update_last_runs_mock.assert_called_with(LAST_RUNS_CSV)
        update_last_runs_mock.assert_called_once()

    @patch('monitors.run_detection.update_last_runs')
    def test_main_lock_timeout(self, _):
        with FileLock('{}.lock'.format(LAST_RUNS_CSV)):
            eorm.main()
