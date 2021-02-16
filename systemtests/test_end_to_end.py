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
import shutil
import time
import unittest
from pathlib import Path

from model.database import access as db
from model.message.message import Message
from queue_processors.queue_processor.queue_listener import main
from scripts.manual_operations import manual_remove as remove
from utils.clients.connection_exception import ConnectionException
from utils.clients.django_database_client import DatabaseClient
from utils.data_archive.data_archive import DataArchive
from utils.project.structure import PROJECT_ROOT

REDUCE_SCRIPT = \
    'def main(input_file, output_dir):\n' \
    '\tprint("WISH system test")\n' \
    '\n' \
    'if __name__ == "__main__":\n' \
    '\tmain()\n'

SYNTAX_ERROR_REDUCE_SCRIPT = \
    'def main(input_file, output_dir):\n' \
    '\tprint("WISH system test\n' \
    '\n' \
    'if __name__ == "__main__":\n' \
    '\tmain()\n'

VARS_SCRIPT = """
standard_vars={"variable1":"value1"}
"""


class TestEndToEnd(unittest.TestCase):
    """ Class to test pipelines in autoreduction"""
    def setUp(self):
        """ Start all external services """
        # Get all clients
        self.database_client = DatabaseClient()
        self.database_client.connect()
        try:
            self.queue_client, self.listener = main()
        except ConnectionException as err:
            raise RuntimeError("Could not connect to ActiveMQ - check you credentials. If running locally check that "
                               "ActiveMQ is running and started by `python setup.py start`") from err
        # Create test archive and add data
        # Add placeholder variables:
        # these are used to ensure runs are deleted even if test fails before completion
        self.instrument = 'ARMI'
        self.rb_number = 1234567
        self.run_number = 101

    def tearDown(self):
        """ Disconnect from services, stop external services and delete data archive """
        self.queue_client.disconnect()
        self.database_client.disconnect()
        self._remove_run_from_database(self.instrument, self.run_number)
        self.data_archive.delete()

        self._delete_reduction_directory()

    def _setup_data_structures(self, reduce_script, vars_script):
        """
        Sets up a fake archive and reduced data save location on the system
        :param reduce_script: The content to use in the reduce.py file
        :param vars_script:  The content to use in the reduce_vars.py file
        :return: file_path to the reduced data
        """
        raw_file = '{}{}.nxs'.format(self.instrument, self.run_number)
        self.data_archive = DataArchive([self.instrument], 19, 19)
        self.data_archive.create()
        self.data_archive.add_reduction_script(self.instrument, reduce_script)
        self.data_archive.add_reduce_vars_script(self.instrument, vars_script)
        raw_file = self.data_archive.add_data_file(self.instrument, raw_file, 19, 1)
        return raw_file

    def _find_run_in_database(self):
        """
        Find a ReductionRun record in the database
        This includes a timeout to wait for several seconds to ensure the database has received
        the record in question
        :return: The resulting record
        """
        instrument = db.get_instrument(self.instrument)
        return instrument.reduction_runs.filter(run_number=self.run_number)

    @staticmethod
    def _remove_run_from_database(instrument, run_number):
        """
        Uses the scripts.manual_operations.manual_remove script
        to remove records added to the database
        """
        if not isinstance(run_number, list):
            run_number = [run_number]
        for run in run_number:
            remove.remove(instrument, run, delete_all_versions=True)

    @staticmethod
    def _delete_reduction_directory():
        """ Delete the temporary reduction directory"""
        path = Path(os.path.join(PROJECT_ROOT, 'reduced-data'))
        if path.exists():
            shutil.rmtree(path.absolute())

    def send_and_wait_for_result(self, message):
        """Sends the message to the queue and waits until the listener has finished processing it"""
        # forces the is_processing to return True so that the listener has time to actually start processing the message
        self.listener._processing = True  #pylint:disable=protected-access
        self.queue_client.send('/queue/DataReady', message)
        while self.listener.is_processing_message():
            time.sleep(0.5)

        # Get Result from database
        results = self._find_run_in_database()

        assert results
        return results

    def test_end_to_end_wish_invalid_rb_number_skipped(self):
        """
        Test that data gets skipped when the RB Number doesn't validate
        """
        # Set meta data for test
        self.rb_number = 222

        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script='')

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=str(file_location),
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        results = self.send_and_wait_for_result(data_ready_message)

        # Validate
        self.assertEqual(self.instrument, results[0].instrument.name)
        self.assertEqual(self.rb_number, results[0].experiment.reference_number)
        self.assertEqual(self.run_number, results[0].run_number)
        self.assertEqual('Skipped', results[0].status.value_verbose())

    def test_end_to_end_wish_completed(self):
        """
        Test that runs gets completed when everything is OK
        """
        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script='')

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        results = self.send_and_wait_for_result(data_ready_message)

        # Validate
        self.assertEqual(self.instrument, results[0].instrument.name)
        self.assertEqual(self.rb_number, results[0].experiment.reference_number)
        self.assertEqual(self.run_number, results[0].run_number)
        self.assertEqual('Completed', results[0].status.value_verbose())

    def test_end_to_end_wish_bad_script_syntax_error(self):
        """
        Test that run gets marked as error when the script has a syntax error
        """
        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=SYNTAX_ERROR_REDUCE_SCRIPT, vars_script='')

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        results = self.send_and_wait_for_result(data_ready_message)

        # Validate
        self.assertEqual(self.instrument, results[0].instrument.name)
        self.assertEqual(self.rb_number, results[0].experiment.reference_number)
        self.assertEqual(self.run_number, results[0].run_number)
        self.assertEqual('Error', results[0].status.value_verbose())

        self.assertIn("REDUCTION Error", results[0].message)
        self.assertIn("Error encountered when running the reduction script", results[0].message)
        self.assertIn("SyntaxError('EOL while scanning string literal'", results[0].message)

    def test_end_to_end_wish_bad_script_raises_exception(self):
        """
        Test that WISH data goes through the system without issue
        """
        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script="raise ValueError('hello from the other side')",
                                                    vars_script='')

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        results = self.send_and_wait_for_result(data_ready_message)

        # Validate
        self.assertEqual(self.instrument, results[0].instrument.name)
        self.assertEqual(self.rb_number, results[0].experiment.reference_number)
        self.assertEqual(self.run_number, results[0].run_number)
        self.assertEqual('Error', results[0].status.value_verbose())
        self.assertIn('ValueError', results[0].message)
        self.assertIn('hello from the other side', results[0].message)

    def test_end_to_end_wish_vars_script_gets_new_variable(self):
        """Test running the same run twice, but the second time the reduce_vars has a new variable"""
        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script='')

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        result_one = self.send_and_wait_for_result(data_ready_message)

        assert len(result_one) == 1
        run_without_vars = result_one[0]

        self.data_archive.add_reduce_vars_script(self.instrument, VARS_SCRIPT)
        result_two = self.send_and_wait_for_result(data_ready_message)

        assert len(result_two) == 2
        assert run_without_vars == result_two[0]  # check that the first run is queried again

        run_with_vars = result_two[1]
        assert run_without_vars.run_variables.count() == 0
        assert run_with_vars.run_variables.count() == 1  # the one standard variable in the VARS_SCRIPT
        var = run_with_vars.run_variables.first().variable
        assert var.name == "variable1"
        assert var.value == "value1"

    def test_end_to_end_wish_vars_script_loses_variable(self):
        """Test running the same run twice, but the second time the reduce_vars has one less variable"""
        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script=VARS_SCRIPT)

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        result_one = self.send_and_wait_for_result(data_ready_message)

        assert len(result_one) == 1
        run_with_vars = result_one[0]
        assert run_with_vars.run_variables.count() == 1  # the one standard variable in the VARS_SCRIPT
        var = run_with_vars.run_variables.first().variable
        assert var.name == "variable1"
        assert var.value == "value1"

        self.data_archive.add_reduce_vars_script(self.instrument, "")
        result_two = self.send_and_wait_for_result(data_ready_message)

        assert len(result_two) == 2
        assert run_with_vars == result_two[0]
        run_without_vars = result_two[1]
        assert run_without_vars.run_variables.count() == 0

    def test_end_to_end_vars_script_has_variable_value_changed(self):
        """Test that reducing the same run after changing the reduce_vars updates the variable's value"""
        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script=VARS_SCRIPT)

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        result_one = self.send_and_wait_for_result(data_ready_message)

        assert len(result_one) == 1
        run_with_initial_var = result_one[0]
        assert run_with_initial_var.run_variables.count() == 1  # the one standard variable in the VARS_SCRIPT
        var = run_with_initial_var.run_variables.first().variable
        assert var.name == "variable1"
        assert var.value == "value1"

        self.data_archive.add_reduce_vars_script(self.instrument, 'standard_vars={"variable1": 123}')
        result_two = self.send_and_wait_for_result(data_ready_message)

        assert len(result_two) == 2
        assert run_with_initial_var == result_two[0]

        run_with_changed_var = result_two[1]

        assert run_with_initial_var.run_variables.count() == 1
        assert run_with_changed_var.run_variables.count() == 1

        initial_var = run_with_initial_var.run_variables.first().variable
        changed_var = run_with_changed_var.run_variables.first().variable

        assert initial_var == changed_var

    def test_end_to_end_wish_vars_script_has_variable_reused_on_new_run_number(self):
        """Test that the variables are reused on new run numbers, IF their value has not changed"""
        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script=VARS_SCRIPT)

        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        result_one = self.send_and_wait_for_result(data_ready_message)

        run_with_initial_var = result_one[0]

        data_ready_message.run_number = 1234568
        result_two = self.send_and_wait_for_result(data_ready_message)
        run_with_different_run_number = result_two[0]

        assert run_with_initial_var.run_variables.count() == 1
        assert run_with_different_run_number.run_variables.count() == 1

        initial_var = run_with_initial_var.run_variables.first().variable
        new_var = run_with_different_run_number.run_variables.first().variable

        assert initial_var == new_var

    def test_end_to_end_wish_vars_script_has_variable_copied_on_new_run_number_when_value_changed(self):
        """Test that the variable is copied for a new run WHEN it's value has been changed"""
        # Create supporting data structures e.g. Data Archive, Reduce directory
        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script=VARS_SCRIPT)

        self.run_number = 101
        # Create and send json message to ActiveMQ
        data_ready_message = Message(rb_number=self.rb_number,
                                     instrument=self.instrument,
                                     data=file_location,
                                     run_number=self.run_number,
                                     facility="ISIS",
                                     started_by=0)

        result_one = self.send_and_wait_for_result(data_ready_message)

        assert len(result_one) == 1
        run_with_initial_var = result_one[0]
        assert run_with_initial_var.run_variables.count() == 1  # the one standard variable in the VARS_SCRIPT
        var = run_with_initial_var.run_variables.first().variable
        assert var.name == "variable1"
        assert var.value == "value1"

        # update the run number in the class because it's used to query for the correct run
        data_ready_message.run_number = self.run_number = 102
        self.data_archive.add_reduce_vars_script(self.instrument, 'standard_vars={"variable1": 123}')
        result_two = self.send_and_wait_for_result(data_ready_message)

        # making the run_number a list so that they can be deleted by the tearDown!
        self.run_number = [101, 102]

        assert len(result_two) == 1

        run_with_changed_var = result_two[0]

        assert run_with_initial_var.run_variables.count() == 1
        assert run_with_changed_var.run_variables.count() == 1

        initial_var = run_with_initial_var.run_variables.first().variable
        changed_var = run_with_changed_var.run_variables.first().variable

        assert initial_var != changed_var
        assert initial_var.name == changed_var.name
        assert initial_var.value != changed_var.value
        assert initial_var.type != changed_var.type
        assert initial_var.instrumentvariable.start_run < changed_var.instrumentvariable.start_run
