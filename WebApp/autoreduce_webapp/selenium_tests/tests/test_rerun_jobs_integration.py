# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import time

from django.urls import reverse
from selenium_tests.pages.rerun_jobs_page import RerunJobsPage
from selenium_tests.tests.base_tests import (BaseTestCase, FooterTestMixin, NavbarTestMixin)
from systemtests.utils.data_archive import DataArchive
from utils.clients.connection_exception import ConnectionException
from utils.clients.django_database_client import DatabaseClient
from model.database import access as db
from queue_processors.queue_processor.queue_listener import main


class TestRerunJobsPageIntegration(NavbarTestMixin, BaseTestCase, FooterTestMixin):

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

    def setUp(self) -> None:
        super().setUp()
        self.page = RerunJobsPage(self.driver, self.instrument_name)
        self.page.launch()

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

    def test_submit_rerun_same_variables(self):
        """
        Test: Just opening the submit page and clicking rerun
        """
        self.page.submit_button.click()
        result = self.wait_for_result()
        assert len(result) == 2

        assert result[0].run_version == 0
        assert result[1].run_version == 1

        for run0_var, run1_var in zip(result[0].run_variables.all(), result[1].run_variables.all()):
            assert run0_var.variable == run1_var.variable

    def test_submit_rerun_changed_variable_arbitrary_value(self):
        """
        Test: Open submit page, change a variable, submit the run
        """
        # change the value of the variable field

        new_value = "the new value in the field"
        self.page.variable1_field = new_value
        self.page.submit_button.click()
        result = self.wait_for_result()
        assert len(result) == 2

        assert result[0].run_version == 0
        assert result[1].run_version == 1

        for run0_var, run1_var in zip(result[0].run_variables.all(), result[1].run_variables.all()):
            # the value of the variable has been overwritten because it's the same run number
            assert run0_var.variable == run1_var.variable

        assert result[1].run_variables.first().variable.value == new_value

    def test_submit_rerun_after_clicking_reset_current_script(self):
        """
        Test: Submitting a run after clicking the "Reset to values in the current reduce_vars script"
              uses the values saved in the current reduce_vars script
        """
        self.page.reset_to_current_values.click()
        self.submit_after_reset()
        result = self.wait_for_result()
        assert len(result) == 2

        assert result[0].run_version == 0
        assert result[1].run_version == 1

        for run0_var, run1_var in zip(result[0].run_variables.all(), result[1].run_variables.all()):
            # the value of the variable has been overwritten because it's the same run number
            assert run0_var.variable == run1_var.variable

        assert result[1].run_variables.first().variable.value == "test_variable_value_123"

    def test_submit_confirm_page(self):
        """
        Test: Submitting a run leads to the correct page
        """
        self.page.submit_button.click()
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})
        assert expected_url in self.driver.current_url
        # wait until the message processing is complete before ending the test
        # otherwise the message handling can polute the DB state for the next test
        result = self.wait_for_result()
        assert len(result) == 2

    def test_empty_run_range(self):
        assert not self.page.form_validation_message.is_displayed()
        self.page.run_range_field = ""
        self.page.submit_button.click()
        assert self.page.form_validation_message.is_displayed()

    def test_invalid_run_range(self):
        assert not self.page.form_validation_message.is_displayed()
        self.page.run_range_field = "-1"
        self.page.submit_button.click()
        assert self.page.form_validation_message.is_displayed()

    def test_non_existent_run_range(self):
        assert not self.page.form_validation_message.is_displayed()
        expected_run = "123123123"
        self.page.run_range_field = expected_run
        self.page.submit_button.click()
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})
        assert expected_url in self.driver.current_url
        assert self.driver.find_element_by_id("error_container").is_displayed()
        assert self.driver.find_element_by_id(
            "error_message").text == f"Run number {expected_run} hasn't been ran by autoreduction yet."
