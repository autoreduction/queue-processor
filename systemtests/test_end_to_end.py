"""
A full end to end system test of the code
This can currently only be tested on Linux: Running this on windows will skip all tests
"""
from __future__ import print_function

import json
import os
import subprocess
import platform
import unittest
import tempfile
import time

import pytest

import git_helpers

from utils.clients.database_client import DatabaseClient
from utils.clients.queue_client import QueueClient
from utils.data_archive.data_archive_creator import DataArchiveCreator
from utils.data_archive.archive_explorer import ArchiveExplorer
from utils.project.structure import get_project_root

import QueueProcessors
from test_helpers import mantid_create_file


@pytest.mark.systemtest
@unittest.skipIf(platform.system() != "Linux", "System test skipped on non-Unix machine")
class TestEndToEnd(unittest.TestCase):
    """
    Tests an end-to-end submission as a system test. This includes adding the run to
    a fake archive to ensure it is correctly processed at the other end
    """
    def setUp(self):
        # Establish connections
        self.queue_connection = QueueClient().connect()
        self.database_connection = DatabaseClient().connect()

        # Flush database

        # Create data archive
        path_to_test_dir = get_project_root()
        self.data_archive_creator = DataArchiveCreator(path_to_test_dir)
        self.archive_explorer = ArchiveExplorer(os.path.join(path_to_test_dir, 'data-archive'))

        # Start QueueProcessors
        start_script = os.path.join(os.path.dirname(os.path.abspath(QueueProcessors.__file__)),
                                    '.', 'restart.sh')

        git_root = git_helpers.get_git_root()
        subprocess.Popen([start_script], cwd=git_root)

    @staticmethod
    def _monitor_file(original_modified_time, file_path):
        timeout = 10  # seconds

        time_start = time.time()
        while time.time() < time_start + timeout:
            if os.path.getmtime(file_path) > original_modified_time:
                return True
            time.sleep(1)
        return False

    def test_gem_end_to_end(self):
        """
        Tests a GEM file can be processed by the autoreduction service
        """
        # Add data to file and reduce script
        temp_file = tempfile.NamedTemporaryFile()
        original_m_time = os.path.getmtime(temp_file.name)
        test_script = mantid_create_file.get_source_str(temp_file.name)

        self.data_archive_creator.make_data_archive(["GEM"], 17, 18, 2)
        self.data_archive_creator.add_data_to_most_recent_cycle("GEM", ['GEM123.raw'])
        self.data_archive_creator.add_reduce_file("GEM", test_script)
        self.data_archive_creator.add_reduce_vars_file("GEM", "")
        # Send data to queue
        data_loc = os.path.join(self.archive_explorer.get_current_cycle_directory("GEM"),
                                'GEM123.raw')
        send_data_to_queue("1", "GEM", data_loc, "123", self.queue_connection)

        # check that the file has been successfully reduced in the db

        self.assertTrue(self._monitor_file(original_m_time, temp_file.name),
                        "GEM File not processed in system test")


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
