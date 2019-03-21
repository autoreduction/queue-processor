# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Linux only!
Tests that data can traverse through the autoreduction system successfully
"""
from __future__ import print_function
import os
import unittest
import json
import time
import shutil

from systemtests import service_handling as external

from utils.test_settings import MYSQL_SETTINGS, ACTIVEMQ_SETTINGS
from utils.clients.database_client import DatabaseClient
from utils.clients.queue_client import QueueClient
from utils.data_archive.data_archive_creator import DataArchiveCreator
from utils.data_archive.archive_explorer import ArchiveExplorer
from utils.project.structure import get_project_root


if os.name != 'nt':
    class TestEndToEnd(unittest.TestCase):
        """ Class to test pipelines in autoreduction"""
	
	@classmethod
        def setUpClass(cls):
	   external.start_activemq()
           external.start_queue_processors()

	def setUp(self):
            """ Start all external services """
            # Start all services
            #external.start_activemq()
            #external.start_queue_processors()
            # Get all clients
            self.database_client = DatabaseClient(MYSQL_SETTINGS)
            self.database_client.connect()
            self.queue_client = QueueClient(ACTIVEMQ_SETTINGS)
            self.queue_client.connect()
            # Create test archive and add data
            self.data_archive_creator = DataArchiveCreator(os.path.join(get_project_root()))
            self.archive_explorer = ArchiveExplorer(os.path.join(get_project_root(),
                                                                 'data-archive'))

        def test_end_to_end_wish(self):
            """ Test that WISH data goes through the system without issue """
            # Add specific data to archive
            self.data_archive_creator.make_data_archive(['WISH'], 19, 19, 1)
            self.data_archive_creator.add_reduce_script(
                'WISH',
                'def main(input_file, output_dir):\n'
                '\tprint("WISH system test")\n'
                '\n'
                'if __name__ == "__main__":\n'
                '\tmain()\n'
            )
            self.data_archive_creator.add_reduce_vars_script('WISH', '')
            self.data_archive_creator.add_data_to_most_recent_cycle('WISH', 'WISH101.nxs')

            # Make temporary location to add reduced files to
            self._make_reduction_directory('WISH', '222', '101')

            # Submit message to activemq
            cycle_path = self.archive_explorer.get_cycle_directory('WISH', 19, 1)
            file_location = os.path.join(cycle_path, 'WISH101.nxs')
            data_ready_message = self.queue_client.serialise_data(rb_number=222,
                                                                  instrument='WISH',
                                                                  location=file_location,
                                                                  run_number=101)
            json_message = json.dumps(data_ready_message)
            self.queue_client.send('/queue/DataReady', json_message)

            results = self._find_run_in_database('WISH', 101)

            # Validate
            self.assertEqual(101, results[0].run_number)
            self.assertEqual(222, results[0].experiment.reference_number)
            self.assertEqual('WISH', results[0].instrument.name)
            self.assertEqual('Completed', results[0].status.value)  # 4 is the id for `Completed`

        def test_wish_user_script_failure(self):
            """ Test that WISH data goes through the system without issue """
            # Add specific data to archive
            self.data_archive_creator.make_data_archive(['WISH'], 19, 19, 1)
            self.data_archive_creator.add_reduce_script('WISH', 'failure')
            self.data_archive_creator.add_reduce_vars_script('WISH', '')
            self.data_archive_creator.add_data_to_most_recent_cycle('WISH', 'WISH102.nxs')

            # Make temporary location to add reduced files to
            self._make_reduction_directory('WISH', '222', '102')

            # Submit message to activemq
            cycle_path = self.archive_explorer.get_cycle_directory('WISH', 19, 1)
            file_location = os.path.join(cycle_path, 'WISH102.nxs')
            data_ready_message = self.queue_client.serialise_data(rb_number=222,
                                                                  instrument='WISH',
                                                                  location=file_location,
                                                                  run_number=102)
            json_message = json.dumps(data_ready_message)
            self.queue_client.send('/queue/DataReady', json_message)

            results = self._find_run_in_database('WISH', 102)

            # Validate
            self.assertEqual(102, results[0].run_number)
            self.assertEqual(222, results[0].experiment.reference_number)
            self.assertEqual('WISH', results[0].instrument.name)
            self.assertEqual('Error', results[0].status.value)  # 4 is the id for `Completed`

        @staticmethod
        def _make_reduction_directory(instrument, rb_number, run_number):
            """
            Make a directory in the expected location for reduced runs to be written to
            """
            reduced_dir = os.path.join(get_project_root(), 'reduced-data')
            reduced_inst = os.path.join(reduced_dir, instrument)
            reduced_rb = os.path.join(reduced_inst, 'RB{}'.format(rb_number))
            reduced_auto = os.path.join(reduced_rb, 'autoreduced')
            reduced_run = os.path.join(reduced_auto, str(run_number))
            os.mkdir(reduced_dir)
            os.mkdir(reduced_inst)
            os.mkdir(reduced_rb)
            os.mkdir(reduced_auto)
            os.mkdir(reduced_run)

        def _find_run_in_database(self, instrument, run_number):
            """
            Find a ReductionRun record in the database
            This includes a timeout to wait for several seconds to ensure the database has recieved
            the record in question
            :param instrument: The name of the instrument associated with the run
            :param run_number: The run number associated with the reduction job
            :return: The resulting record
            """
            wait_times = [0, 2, 5, 10, 20]
            results = []
            for timeout in wait_times:
                # Wait before attempting database access
                print('Waiting for: {}'.format(timeout))
                time.sleep(timeout)
                # Check database has expected values
                connection = self.database_client.get_connection()
                results = connection.query(self.database_client.reduction_run()) \
                    .join(self.database_client.reduction_run().instrument) \
                    .join(self.database_client.reduction_run().status) \
                    .join(self.database_client.reduction_run().experiment) \
                    .filter(self.database_client.instrument().name == instrument) \
                    .filter(self.database_client.reduction_run().run_number == run_number).all()
                connection.commit()
                try:
                    actual = results[0]
                except IndexError:
                    # If no results found yet then continue
                    continue
                if actual.status.value == 'Completed' or actual.status.value == 'Error':
                    print('Job reached {} status after {} seconds'.format(actual.status.value,
                                                                          timeout))
                    break
            return results

        @staticmethod
        def _delete_reduction_directory():
            """ Delete the temporary reduction directory"""
            shutil.rmtree(os.path.join(get_project_root(), 'reduced-data'))

        def tearDown(self):
            """ Disconnect from services, stop external services and delete data archive """
            self.queue_client.disconnect()
            self.database_client.disconnect()
            #external.stop_activemq()
            #external.stop_queue_processors()
            self._delete_reduction_directory()
            del self.data_archive_creator

	@classmethod
	def tearDownClass(cls):
	   external.stop_activemq()
	   external.stop_queue_processors()

else:
    class TestEndToEnd(unittest.TestCase):
        """
        This will be skipped on windows
        """

        @unittest.skip("System test skipped on windows")
        def test_windows(self):
            """
            Just Skip on windows
            function is here to make it more obvious that tests are not for windows
            """
            pass
