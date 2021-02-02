# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Linux only!
Tests that data can traverse through the autoreduction system successfully
"""

import os
import unittest
import time
import shutil

from model.database import access as db
from model.message.message import Message

from scripts.manual_operations import manual_remove as remove

from utils.settings import ACTIVEMQ_SETTINGS
from utils.clients.django_database_client import DatabaseClient
from utils.clients.queue_client import QueueClient
from utils.data_archive.data_archive_creator import DataArchiveCreator
from utils.data_archive.archive_explorer import ArchiveExplorer
from utils.project.structure import get_project_root

from utils.clients.connection_exception import ConnectionException

REDUCE_SCRIPT = \
    'def main(input_file, output_dir):\n' \
    '\tprint("WISH system test")\n' \
    '\n' \
    'if __name__ == "__main__":\n' \
    '\tmain()\n'


class TestEndToEnd(unittest.TestCase):
    """ Class to test pipelines in autoreduction"""
    def setUp(self):
        """ Start all external services """
        # Get all clients
        self.database_client = DatabaseClient()
        self.database_client.connect()
        self.queue_client = QueueClient(ACTIVEMQ_SETTINGS)
        try:
            self.queue_client.connect()
        except ConnectionException as err:
            raise RuntimeError("Could not connect to ActiveMQ - check you credentials. If running locally check that "
                               "ActiveMQ is running and started by `python setup.py start`") from err
        # Create test archive and add data
        self.data_archive_creator = DataArchiveCreator(os.path.join(get_project_root()), overwrite=True)
        self.archive_explorer = ArchiveExplorer(os.path.join(get_project_root(), 'data-archive'))
        # Add placeholder variables:
        # these are used to ensure runs are deleted even if test fails before completion
        self.instrument = None
        self.rb_number = None
        self.run_number = None

    def tearDown(self):
        """ Disconnect from services, stop external services and delete data archive """
        self.queue_client.disconnect()
        self.database_client.disconnect()
        self._delete_reduction_directory()
        del self.data_archive_creator
        # Done in tearDown to ensure run is removed even if test fails early
        self._remove_run_from_database(self.instrument, self.run_number)

    def test_end_to_end_wish(self):
        """
        Test that WISH data goes through the system without issue
        """
        # Set meta data for test
        self.instrument = 'WISH'
        self.rb_number = 222
        self.run_number = 101

        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script='')

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        self.queue_client.send('/queue/DataReady', data_ready_message)

        # Get Result from database
        results = self._find_run_in_database()

        # Validate
        self.assertEqual(self.instrument, results[0].instrument.name)
        self.assertEqual(self.rb_number, results[0].experiment.reference_number)
        self.assertEqual(self.run_number, results[0].run_number)
        self.assertEqual('Completed', results[0].status.value_verbose())

#         def test_wish_user_script_failure(self):
#             """
#             Test that WISH data goes through the system without issue
#             """
#             # Set meta data for test
#             self.instrument = 'WISH'
#             self.rb_number = 222
#             self.run_number = 101

#             # Create supporting data structures e.g. Data Archive, Reduce directory
#             file_location = self._setup_data_structures(reduce_script='fail', vars_script='')

#             # Create and send json message to ActiveMQ
#             data_ready_message = Message(rb_number=self.rb_number,
#                                          instrument=self.instrument,
#                                          data=file_location,
#                                          run_number=self.run_number,
#                                          facility="ISIS",
#                                          started_by=0)

#             self.queue_client.send('/queue/DataReady', data_ready_message)

#             # Get Result from database
#             results = self._find_run_in_database()

#             # Validate
#             self.assertEqual(self.instrument, results[0].instrument.name)
#             self.assertEqual(self.rb_number, results[0].experiment.reference_number)
#             self.assertEqual(self.run_number, results[0].run_number)
#             self.assertEqual('e', results[0].status.value)  # verbose value = "Error"

    def _setup_data_structures(self, reduce_script, vars_script):
        """
        Sets up a fake archive and reduced data save location on the system
        :param reduce_script: The content to use in the reduce.py file
        :param vars_script:  The content to use in the reduce_vars.py file
        :return: file_path to the reduced data
        """
        raw_file = '{}{}.nxs'.format(self.instrument, self.run_number)
        # Create and add data to archive
        self.data_archive_creator.make_data_archive([self.instrument], 19, 19, 1)
        self.data_archive_creator.add_reduce_script(instrument=self.instrument, file_content=reduce_script)
        self.data_archive_creator.add_reduce_vars_script(self.instrument, vars_script)
        self.data_archive_creator.add_data_to_most_recent_cycle(self.instrument, raw_file)

        # Make temporary location to add reduced files to
        # self._make_reduction_directory(self.instrument, self.rb_number, self.run_number)

        # Submit message to activemq
        cycle_path = self.archive_explorer.get_cycle_directory(self.instrument, 19, 1)
        return os.path.join(cycle_path, raw_file)

    # @staticmethod
    # def _make_reduction_directory(instrument, rb_number, run_number):
    #     """
    #     Make a directory in the expected location for reduced runs to be written to
    #     """
    #     reduced_dir = os.path.join(get_project_root(), 'reduced-data')
    #     reduced_inst = os.path.join(reduced_dir, str(instrument))
    #     reduced_rb = os.path.join(reduced_inst, 'RB{}'.format(str(rb_number)))
    #     reduced_auto = os.path.join(reduced_rb, 'autoreduced')
    #     reduced_run = os.path.join(reduced_auto, str(run_number))
    #     os.mkdir(reduced_dir)
    #     os.mkdir(reduced_inst)
    #     os.mkdir(reduced_rb)
    #     os.mkdir(reduced_auto)
    #     os.mkdir(reduced_run)

    def _find_run_in_database(self):
        """
        Find a ReductionRun record in the database
        This includes a timeout to wait for several seconds to ensure the database has received
        the record in question
        :return: The resulting record
        """
        wait_times = [0, 1, 2, 3, 5]
        results = []
        for timeout in wait_times:
            # Wait before attempting database access
            print(f"Waiting for: {timeout}")
            time.sleep(timeout)
            # Check database has expected values
            instrument_record = db.get_instrument(self.instrument)
            results = self.database_client.data_model.ReductionRun.objects \
                .filter(instrument=instrument_record.id) \
                .filter(run_number=self.run_number) \
                .select_related() \
                .all()
            try:
                actual = results[0]
            except IndexError:
                # If no results found yet then continue
                continue

            # verbose values = "Completed" or "Error"
            if actual.status.value == 'c' or actual.status.value == 'e':
                print(f"Job reached {actual.status.value} status after {timeout} seconds")
                break

        return results

    @staticmethod
    def _remove_run_from_database(instrument, run_number):
        """
        Uses the scripts.manual_operations.manual_remove script
        to remove records added to the database
        """
        remove.remove(instrument, run_number, delete_all_versions=False)

    @staticmethod
    def _delete_reduction_directory():
        """ Delete the temporary reduction directory"""
        shutil.rmtree(os.path.join(get_project_root(), 'reduced-data'))


#         @classmethod
#         def tearDownClass(cls):
#             # Stop external services
#             external.stop_queue_processors()
