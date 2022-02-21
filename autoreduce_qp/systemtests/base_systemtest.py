# ############################################################################### #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Linux only! Tests that data can traverse through the Autoreduction system
successfully.
"""
# pylint:disable=no-member
import os
import shutil
import time
from pathlib import Path

from django.test import TransactionTestCase

from autoreduce_db.reduction_viewer.models import Instrument, ReductionRun
from autoreduce_utils.clients.connection_exception import ConnectionException
from autoreduce_utils.message.message import Message
from autoreduce_utils.settings import MANTID_PATH, PROJECT_DEV_ROOT
from autoreduce_qp.queue_processor.confluent_consumer import setup_kafka_connections
from autoreduce_qp.systemtests.utils.data_archive import DataArchive
from autoreduce_qp.model.database import access as db

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

FAKE_MANTID = """
__version__ = "5.1.0"
"""


class BaseAutoreduceSystemTest(TransactionTestCase):
    """Tests that the Queue Listener reconnects after ActiveMQ goes down"""
    fixtures = ["status_fixture"]

    def setUp(self):
        """ Start all external services """
        # Get all clients
        try:
            self.publisher, self.consumer = setup_kafka_connections()
        except ConnectionException as err:
            raise RuntimeError("Could not connect to Kafka - check your credentials. If running locally check that "
                               "the Kafka Docker container is running") from err
        # Add placeholder variables:
        # these are used to ensure runs are deleted even if test fails before completion
        self.instrument = 'ARMI'
        self.instrument_obj, _ = Instrument.objects.get_or_create(name=self.instrument, is_active=True)
        self.rb_number = 1234567
        self.run_number = 101
        self.run_title = "test title"
        self.software = {
            "name": "Mantid",
            "version": "6.2.0",
        }

        # Create test archive and add data
        self.data_archive = DataArchive([self.instrument], 19, 19)
        self.data_archive.create()

        # Create and send json message to Kafka
        self.data_ready_message = Message(rb_number=self.rb_number,
                                          instrument=self.instrument,
                                          run_number=self.run_number,
                                          run_title=self.run_title,
                                          description="This is a system test",
                                          facility="ISIS",
                                          software=self.software,
                                          started_by=0,
                                          reduction_script=None,
                                          reduction_arguments=None)

        if self.software.get("name") == "Mantid":
            expected_mantid_py = f"{MANTID_PATH}/mantid.py"
            if not os.path.exists(expected_mantid_py):
                os.makedirs(MANTID_PATH)
                with open(expected_mantid_py, mode="w", encoding="utf-8") as self.test_mantid_py:
                    self.test_mantid_py.write(FAKE_MANTID)
            else:
                # Mantid is installed, don't create or delete (in tearDown) anything
                self.test_mantid_py = None

    def tearDown(self):
        """ Disconnect from services, stop external services and delete data archive """
        self.consumer.stop()
        self._remove_run_from_database(self.instrument, self.run_number)
        self.data_archive.delete()

        self._delete_reduction_directory()

        if self.test_mantid_py:
            shutil.rmtree(MANTID_PATH)

    @staticmethod
    def _remove_run_from_database(instrument, run_number):
        """
        Uses the scripts.manual_operations.manual_remove script
        to remove records added to the database
        """
        if not isinstance(run_number, list):
            run_number = [run_number]

        ReductionRun.objects.filter(instrument__name=instrument, run_numbers__run_number__in=run_number).delete()

    @staticmethod
    def _delete_reduction_directory():
        """ Delete the temporary reduction directory"""
        path = Path(os.path.join(PROJECT_DEV_ROOT, 'reduced-data'))
        if path.exists():
            shutil.rmtree(path.absolute())

    def _setup_data_structures(self, reduce_script, vars_script):
        """
        Sets up a fake archive and reduced data save location on the system
        :param reduce_script: The content to use in the reduce.py file
        :param vars_script:  The content to use in the reduce_vars.py file
        :return: file_path to the reduced data
        """
        raw_file = f'{self.instrument}{self.run_number}.nxs'
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
        return instrument.reduction_runs.filter(run_numbers__run_number=self.run_number)

    def send_and_wait_for_result(self, message):
        """Sends the message to the topic and waits until the consumer has finished processing it"""
        self.consumer._processing = True  # pylint:disable=protected-access
        self.publisher.publish(topic='data_ready', messages=message)
        start_time = time.time()
        while self.consumer.is_processing_message():
            time.sleep(5)
            if time.time() > start_time + 120:  # Prevent waiting indefinitely and break after 2 minutes
                break
        time.sleep(10)  # Wait for the message to be processed
        results = self._find_run_in_database()
        assert results
        return results
