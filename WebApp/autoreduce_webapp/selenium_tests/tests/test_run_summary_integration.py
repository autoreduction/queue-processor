# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the runs summary page
"""

from django.urls import reverse
from selenium.webdriver.support.ui import WebDriverWait

from model.database import access as db
from queue_processors.queue_processor.queue_listener import main
from selenium_tests.pages.run_summary_page import RunSummaryPage
from selenium_tests.tests.base_tests import (BaseTestCase, FooterTestMixin, NavbarTestMixin)
from systemtests.utils.data_archive import DataArchive
from utils.clients.connection_exception import ConnectionException
from utils.clients.django_database_client import DatabaseClient


class TestRunSummaryPageIntegration(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the InstrumentSummary page when the Rerun form is NOT visible
    """

    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    @classmethod
    def setUpClass(cls):
        """ Start all external services """
        super().setUpClass()
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

        cls.data_archive = DataArchive([cls.instrument_name], 21, 21)
        cls.data_archive.create()
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                """standard_vars={"variable1":"test_variable_value_123"}""")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.queue_client.disconnect()
        cls.database_client.disconnect()
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.page = RunSummaryPage(self.driver, self.instrument_name, 99999, 0)
        self.page.launch()
        # clicks the toggle to show the rerun panel, otherwise the buttons in the form are non interactable
        self.page.toggle_button.click()

    def _find_run_in_database(self):
        """
        Find a ReductionRun record in the database
        This includes a timeout to wait for several seconds to ensure the database has received
        the record in question
        :return: The resulting record
        """
        instrument = db.get_instrument(self.instrument_name)
        return instrument.reduction_runs.filter(run_number=self.run_number)

    def submit_and_wait_for_result(self):
        """Waits until the queue listener has finished processing the current message"""
        # forces the is_processing to return True so that the listener has time to actually start processing the message
        self.listener._processing = True  #pylint:disable=protected-access

        # only then submit, to avoid a deadlock that can happen while waiting
        self.page.submit_button.click()

        WebDriverWait(self.driver, 30).until(lambda _: not self.listener.is_processing_message())

        # Get Result from database
        results = self._find_run_in_database()

        assert results
        return results

    def submit_after_reset_and_wait_for_result(self):
        """
        Submit after a reset button has been clicked. Then waits until the queue listener has finished processing.

        Sticks the submission in a loop in case the first time doesn't work. The reason
        it may not work is that resetting actually swaps out the whole form using JS, which
        replaces ALL the elements and triggers a bunch of DOM re-renders/updates, and that isn't fast.
        """
        self.listener._processing = True  #pylint:disable=protected-access
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})

        def submit_successful(driver) -> bool:
            self.page.submit_button.click()
            # the submit is successful
            return expected_url in driver.current_url

        WebDriverWait(self.driver, 30).until(submit_successful)
        WebDriverWait(self.driver, 30).until(lambda _: not self.listener.is_processing_message())

        # Get Result from database
        results = self._find_run_in_database()

        assert results
        return results

    def test_submit_rerun_same_variables(self):
        """
        Test: Just opening the submit page and clicking rerun
        """
        result = self.submit_and_wait_for_result()
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
        self.page.variable1_field = "the new value in the field"

        result = self.submit_and_wait_for_result()
        assert len(result) == 2

        assert result[0].run_version == 0
        assert result[1].run_version == 1

        for run0_var, run1_var in zip(result[0].run_variables.all(), result[1].run_variables.all()):
            # the value of the variable has been overwritten because it's the same run number
            assert run0_var.variable == run1_var.variable

        assert result[1].run_variables.first().variable.value == "the new value in the field"

    def test_submit_rerun_after_clicking_reset_initial(self):
        """
        Test: Submitting a run after changing the value and then clicking reset to initial values
        will correctly use the initial values
        """
        # change the value of the variable field
        self.page.variable1_field = "the new value in the field"

        self.page.reset_to_initial_values.click()
        result = self.submit_after_reset_and_wait_for_result()
        assert len(result) == 2

        assert result[0].run_version == 0
        assert result[1].run_version == 1

        for run0_var, run1_var in zip(result[0].run_variables.all(), result[1].run_variables.all()):
            # the value of the variable has been overwritten because it's the same run number
            assert run0_var.variable == run1_var.variable

        assert result[1].run_variables.first().variable.value == "value1"

    def test_submit_rerun_after_clicking_reset_current_script(self):
        """
        Test: Submitting a run after clicking the reset to current script uses the values saved in the current script
        """
        self.page.reset_to_current_values.click()
        result = self.submit_after_reset_and_wait_for_result()

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
        result = self.submit_and_wait_for_result()
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})
        assert expected_url in self.driver.current_url
        # wait until the message processing is complete before ending the test
        # otherwise the message handling can polute the DB state for the next test
        assert len(result) == 2
