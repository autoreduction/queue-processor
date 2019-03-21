# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test the InstrumentMonitor that performs the majority of task for the end of run monitor service
"""
import os
import unittest
import threading
import time

from mock import patch
from watchdog.events import FileSystemEvent

from monitors.end_of_run_monitor import (InstrumentMonitor, get_file_extension,
                                         get_data_and_check, stop, main)
from monitors.settings import INSTRUMENTS
from monitors.tests.helpers import TestListener, create_connection
from utils.clients.queue_client import QueueClient
from utils.data_archive.data_archive_creator import DataArchiveCreator
from utils.data_archive.archive_explorer import ArchiveExplorer
from utils.project.structure import get_project_root

import utils.service_handling as external


def raise_exception():
    """ function required to raise Exception in mocks """
    raise Exception('Exception raised from mock')  # pragma: no cover


# pylint:disable=missing-docstring,protected-access
class TestEndOfRunMonitor(unittest.TestCase):

    archive = None
    test_dir = None
    connection = None

    @classmethod
    def setUpClass(cls):
        external.start_activemq()
        # Create data archive in temporary directory and point archive explorer at it
        cls.test_dir = get_project_root()
        cls.archive = DataArchiveCreator(cls.test_dir)
        cls.archive.make_data_archive(['WISH'], 17, 18, 2)
        cls.archive.add_last_run_file('WISH', "WISH 12345 00")
        cls.archive.add_journal_file('WISH', 'summary file metadata then rb: 111')
        cls.explorer = ArchiveExplorer(os.path.join(cls.test_dir, 'data-archive'))

        # Create an instrument monitor
        cls.monitor = InstrumentMonitor('WISH', True, QueueClient(), threading.Lock())
        cls.expected_dict = {
            "rb_number": '111',
            "instrument": 'WISH',
            "data": os.path.join(cls.explorer.get_current_cycle_directory('WISH'),
                                 'WISH12345.nxs'),
            "run_number": "12345",
            "facility": "ISIS"
        }

        # Create connection and listener
        cls.listener = TestListener()
        cls.connection = create_connection(cls.listener)

    def test_get_file_extension(self):
        self.assertEqual(get_file_extension(True), '.nxs')
        self.assertEqual(get_file_extension(False), '.raw')

    def test_get_data_and_check(self):
        with open(self.explorer.get_last_run_file('WISH'), 'r') as last_run:
            data = get_data_and_check(last_run)
        self.assertEqual(data, ['WISH', '12345', '00'])

    def test_invalid_get_data_and_check(self):
        self.archive.make_data_archive(['GEM'], 18, 18, 2)
        self.archive.add_last_run_file('GEM', 'Invalid format for the last run file')
        with open(self.explorer.get_last_run_file('GEM'), 'r') as last_run:
            self.assertRaises(Exception, get_data_and_check, last_run)

    def test_init(self):
        client = QueueClient()
        lock = threading.Lock()
        monitor = InstrumentMonitor('WISH', True, client, lock)
        self.assertIsInstance(monitor, InstrumentMonitor)
        self.assertEqual(monitor.instrument_name, 'WISH')
        self.assertEqual(monitor.use_nexus, True)
        self.assertEqual(monitor.client, client)
        self.assertEqual(monitor.lock, lock)

    def test_get_most_recent_cycle(self):
        cycle = self.monitor._get_most_recent_cycle()
        self.assertEqual(cycle, '18_2')

    def test_get_instrument_data_folder(self):
        data_location = self.monitor._get_instrument_data_folder_loc()
        suffix = os.path.join('NDXWISH', 'Instrument', 'data', 'cycle_18_2')
        self.assertTrue(data_location.endswith(suffix))

    def test_get_rb_number(self):
        rb_number = self.monitor._get_rb_num()
        self.assertEqual(rb_number, '111')

    def test_build_dict(self):
        # input is return value of get_data_and_check
        data_dict = self.monitor.build_dict(['WISH', '12345', '00'])
        self.assertEqual(data_dict, self.expected_dict)

    def test_get_watched_folder(self):
        watched_folder = self.monitor.get_watched_folder()
        suffix = os.path.join('NDXWISH', 'Instrument', 'logs')
        self.assertTrue(watched_folder.endswith(suffix))

    def test_send_message(self):
        self.monitor.send_message(['WISH', '12345', '00'])
        message = self._get_message_from_queues()
        self.assertIsNotNone(message)

    def test_on_modified(self):
        # Update lastrun.txt
        self.archive.overwrite_file_content(self.explorer.get_last_run_file('WISH'),
                                            "WISH 12346 00")
        event = FileSystemEvent(self.explorer.get_last_run_file('WISH'))
        self.monitor.on_modified(event)
        message = self._get_message_from_queues()
        updated_dict = self.expected_dict
        updated_dict["run_number"] = "12346"
        new_data_loc = os.path.join(self.explorer.get_current_cycle_directory('WISH'),
                                    'WISH12346.nxs')
        updated_dict["data"] = new_data_loc
        self.assertEqual(message, updated_dict)

    # pylint:disable=invalid-name
    @patch('logging.exception')
    @patch('logging.debug')
    def test_on_modified_if_exception_raised(self, mock_debug, mock_exception):
        mock_debug.side_effect = raise_exception
        self.monitor.on_modified('test')
        mock_exception.assert_called_once()

    def test_windows_path_split(self):
        current_system = os.name
        os.name = 'nt'
        expected = ['list', 'of', 'files.txt']
        actual = self.monitor.split_path_into_folders(r'list\of\files.txt')
        self.assertEqual(expected, actual)
        os.name = current_system

    def test_path_split(self):
        current_system = os.name
        os.name = 'posix'
        expected = ['list', 'of', 'files.txt']
        actual = self.monitor.split_path_into_folders('list/of/files.txt')
        self.assertEqual(expected, actual)
        os.name = current_system

    # pylint:disable=no-self-use
    @patch('watchdog.observers.Observer.stop')
    @patch('watchdog.observers.Observer.join')
    def test_stop(self, join_mock, stop_mock):
        stop()
        join_mock.assert_called_once()
        stop_mock.assert_called_once()

    @patch('monitors.end_of_run_monitor.InstrumentMonitor.__init__', return_value=None)
    @patch('monitors.end_of_run_monitor.InstrumentMonitor.get_watched_folder',
           return_value='test_path')
    @patch('watchdog.observers.Observer.start')
    @patch('watchdog.observers.Observer.schedule')
    def test_main(self, schedule_mock, start_mock, get_folder_mock, init_mock):
        main()
        self.assertEqual(init_mock.call_count, len(INSTRUMENTS))
        self.assertEqual(get_folder_mock.call_count, len(INSTRUMENTS))
        self.assertEqual(schedule_mock.call_count, len(INSTRUMENTS))
        start_mock.assert_called_once()

    def _get_message_from_queues(self):
        """
        Try for 5 seconds to retrieve message from activeMQ
        Will reset the listener.message to None after message retrieved
        :return: message from activemq or None
        """
        attempts = 0
        # attempt to get the message for 5 seconds (break early if found before then)
        while self.listener.message is None and attempts < 5:
            time.sleep(1)
            attempts += 1
        message = self.listener.message
        self.listener.message = None
        return message

    @classmethod
    def tearDownClass(cls):
        cls.archive.delete_archive()
        cls.connection.disconnect()
        external.stop_activemq()
