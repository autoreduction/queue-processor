"""
A full end to end system test of the code
This can currently only be tested on Linux: Running this on windows will skip all tests
"""
import json
import os
import subprocess
import platform
import unittest

from utils.clients.database_client import DatabaseClient
from utils.clients.queue_client import QueueClient
from utils.test_helpers.data_archive_creator import DataArchiveCreator

import QueueProcessors

if platform.system() != 'Windows':
    class TestEndToEnd(unittest.TestCase):

        def setUp(self):
            # Establish connections
            self.queue_connection = QueueClient().get_connection()
            self.database_connection = DatabaseClient().get_connection()

            # Flush database

            # Create data archive
            os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test'))
            path_to_test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test')
            self.data_archive_creator = DataArchiveCreator(path_to_test_dir)

            # Start QueueProcessors
            subprocess.call(['./' + os.path.join(os.path.abspath(QueueProcessors.__file__),
                                                 'QueueProcessors', 'restart.sh')])

        def test_gem_end_to_end(self):
            send_data_to_queue("1", "GEM", "path/to/file", "000001", self.queue_connection)
            # monitor execution somehow?
            # check that the file has been successfully reduced in the db
            pass

        def test_wish_end_to_end(self):
            send_data_to_queue("2", "WISH", "path/to/file", "000002", self.queue_connection)
            # monitor execution somehow?
            # check that the file has been successfully reduced in the db
            pass
    
        def test_polaris_end_to_end(self):
            send_data_to_queue("3", "POLARIS", "path/to/file", "000003", self.queue_connection)
            # monitor execution somehow?
            # check that the file has been successfully reduced in the db
            pass
    
        def test_polref_end_to_end(self):
            send_data_to_queue("4", "POLREF", "path/to/file", "000004", self.queue_connection)
            # monitor execution somehow?
            # check that the file has been successfully reduced in the db
            pass
    
        def test_osiris_end_to_end(self):
            send_data_to_queue("5", "OSIRIS", "path/to/file", "000005", self.queue_connection)
            # monitor execution somehow?
            # check that the file has been successfully reduced in the db
            pass
else:
    class TestEndToEnd(unittest.TestCase):
        def test_is_windows(self):
            self.skipTest("Unable to run this test on Windows platform")


def send_data_to_queue(rb_number, instrument, location, run_number, queue_processor_connection):
    data_to_send = {'rb_number': rb_number,
                    'instrument': instrument,
                    'data': location,
                    'run_number': run_number,
                    'facility': 'ISIS'}
    queue_processor_connection.send('/queue/DataReady',
                                    json.dumps(data_to_send),
                                    priority='9')
