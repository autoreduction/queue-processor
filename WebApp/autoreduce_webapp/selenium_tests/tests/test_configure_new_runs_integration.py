# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import time
from selenium_tests.pages.variables_summary_page import VariableSummaryPage

from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin
from model.database import access as db
from instrument.models import InstrumentVariable
from systemtests.utils.data_archive import DataArchive
from queue_processors.queue_processor.queue_listener import main
from utils.clients.connection_exception import ConnectionException
from utils.clients.django_database_client import DatabaseClient
from selenium_tests.pages.configure_new_runs_page import ConfigureNewRunsPage
from selenium.common.exceptions import NoSuchElementException


class TestConfigureNewRunsPageIntegration(BaseTestCase):

    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive = DataArchive([cls.instrument_name], 21, 21)
        cls.data_archive.create()
        cls.data_archive.add_reduction_script(cls.instrument_name, """print('some text')""")
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                """standard_vars={"variable1":"test_variable_value_123"}""")
        cls.database_client = DatabaseClient()
        cls.database_client.connect()
        try:
            cls.queue_client, cls.listener = main()
        except ConnectionException as err:
            raise RuntimeError("Could not connect to ActiveMQ - check you credentials. If running locally check that "
                               "ActiveMQ is running and started by `python setup.py start`") from err

        cls.instrument_name = "TestInstrument"
        cls.rb_number = 1234567
        cls.run_number = 99999

    @classmethod
    def tearDownClass(cls) -> None:
        cls.queue_client.disconnect()
        cls.database_client.disconnect()
        cls.data_archive.delete()
        super().tearDownClass()

    def _find_run_in_database(self):
        """
        Find a ReductionRun record in the database
        This includes a timeout to wait for several seconds to ensure the database has received
        the record in question
        :return: The resulting record
        """
        instrument = db.get_instrument(self.instrument_name)
        return instrument.reduction_runs.filter(run_number=self.run_number)

    def wait_for_result(self):
        """Waits until the queue listener has finished processing the current message"""
        # forces the is_processing to return True so that the listener has time to actually start processing the message
        self.listener._processing = True  #pylint:disable=protected-access
        while self.listener.is_processing_message():
            time.sleep(0.5)

        # Get Result from database
        results = self._find_run_in_database()

        assert results
        return results

    def submit_after_reset(self):
        """
        Submit after a reset button has been clicked.

        Sticks the submission in a loop in case the first time doesn't work. The reason
        it may not work is that resetting actually swaps out the whole form using JS, which
        replaces ALL the elements and triggers a bunch of DOM re-renders/updates, and that isn't fast.
        """
        page_url = self.page.url()
        while page_url in self.driver.current_url:
            # NOTE that we MUST wait first and then try to submit, otherwise the processing
            # may be finished before wait_for_result is called, causing it to be stuck forever
            time.sleep(1)
            self.page.submit_button.click()

    # def test_submit_submit_same_variables_does_not_add_new_variables(self):
    #     """
    #     Test: Just opening the submit page and clicking rerun
    #     """
    #     self.page.submit_button.click()
    #     assert InstrumentVariable.objects.count() == 1

    #     summary = VariableSummaryPage(self.driver, self.instrument_name)
    #     assert summary.current_variables_by_run.is_displayed()

    #     with self.assertRaises(NoSuchElementException):
    #         summary.upcoming_variables_by_run.is_displayed()
    #     with self.assertRaises(NoSuchElementException):
    #         summary.upcoming_variables_by_experiment.is_displayed()

    # def test_submit_new_value(self):
    #     """
    #     Test: Just opening the submit page and clicking rerun
    #     """
    #     self.page.variable1_field = "new_value"
    #     self.page.submit_button.click()
    #     assert InstrumentVariable.objects.count() == 2
    #     new_var = InstrumentVariable.objects.last()
    #     assert new_var.start_run == self.run_number + 1
    #     assert new_var.value == "new_value"

    #     summary = VariableSummaryPage(self.driver, self.instrument_name)
    #     assert summary.current_variables_by_run.is_displayed()
    #     assert summary.upcoming_variables_by_run.is_displayed()

    #     with self.assertRaises(NoSuchElementException):
    #         summary.upcoming_variables_by_experiment.is_displayed()

    def test_submit_experiment_var(self):
        self.page = ConfigureNewRunsPage(self.driver, self.instrument_name, experiment_reference=self.rb_number)
        self.page.launch()
        self.page.variable1_field = "new_value"
        self.page.submit_button.click()
        assert InstrumentVariable.objects.count() == 2
        new_var = InstrumentVariable.objects.last()
        assert new_var.start_run is None
        assert new_var.experiment_reference == self.rb_number
        assert new_var.value == "new_value"

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_experiment.is_displayed()

        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_run.is_displayed()

    # def test_submit_multiple_run_ranges
    # def test_submit_multiple_experiments
    # def test_submit_multiple_run_ranges_and_then_experiment
    # ??