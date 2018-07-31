"""
A full end to end system test of the code
This can currently only be tested on Linux: Running this on windows will skip all tests
"""
import json
import os
import subprocess
import time
import platform
import unittest
import pytest

from utils.clients.database_client import DatabaseClient
from utils.clients.queue_client import QueueClient
from utils.test_helpers.data_archive_creator import DataArchiveCreator

import QueueProcessors

TEST_SCRIPT = "def main(input_file, output_dir):\n" \
              "   print('hello world')\n" \
              "\n"


@pytest.mark.systemtest
@unittest.skipIf(platform.system() != "Linux", "System test skipped on non-Unix machine")
class TestEndToEnd(unittest.TestCase):
    """
    Tests an end-to-end submission as a system test. This includes adding the run to
    a fake archive to ensure it is correctly processed at the other end
    """
    def setUp(self):
        # Establish connections
        self.queue_connection = QueueClient().get_connection()
        self.database_connection = DatabaseClient().get_connection()

        # Flush database

        # Create data archive
        path_to_test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        self.data_archive_creator = DataArchiveCreator(path_to_test_dir)

        # Start QueueProcessors
        start_script = os.path.join(os.path.dirname(os.path.abspath(QueueProcessors.__file__)),
                                    '.', 'restart.sh')
        subprocess.call([start_script])

    def test_gem_end_to_end(self):
        """
        Tests a GEM file can be processed by the autoreduction service
        """
        # Add data to file and reduce script
        self.data_archive_creator.make_data_archive(["GEM"], 17, 18, 2)
        self.data_archive_creator.add_data_to_most_recent_cycle("GEM", ['GEM123.raw'])
        self.data_archive_creator.add_reduce_file("GEM", TEST_SCRIPT)
        self.data_archive_creator.add_reduce_vars_file("GEM", "")
        # Send data to queue
        data_loc = os.path.join(self.data_archive_creator.get_current_cycle_for_inst("GEM"),
                                'GEM123.raw')
        send_data_to_queue("1", "GEM", data_loc, "123", self.queue_connection)
        # check that the file has been successfully reduced in the db
        time.sleep(5)


def send_data_to_queue(rb_number, instrument, location, run_number, queue_processor_connection):
    """
    Packs the specified data into a dictionary ready to send to a processor queue
    """
    data_to_send = {'rb_number': rb_number,
                    'instrument': instrument,
                    'data': location,
                    'run_number': run_number,
                    'facility': 'ISIS'}
    queue_processor_connection.send('/queue/DataReady',
                                    json.dumps(data_to_send),
                                    priority='9')
