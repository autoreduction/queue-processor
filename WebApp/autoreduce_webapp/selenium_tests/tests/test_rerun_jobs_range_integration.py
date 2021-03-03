# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import time

from django.urls import reverse
from selenium_tests.pages.rerun_jobs_page import RerunJobsPage
from selenium_tests.pages.run_summary_page import RunSummaryPage
from selenium_tests.pages.runs_list_page import RunsListPage
from selenium_tests.tests.base_tests import (BaseTestCase, FooterTestMixin, NavbarTestMixin)

from queue_processors.queue_processor.queue_listener import main
from utils.clients.connection_exception import ConnectionException
from utils.clients.django_database_client import DatabaseClient
from model.database import access as db
from systemtests.utils.data_archive import DataArchive


class TestRerunJobsRangePageIntegration(NavbarTestMixin, BaseTestCase, FooterTestMixin):

    fixtures = BaseTestCase.fixtures + ["two_runs"]

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
        cls.run_number = [99999, 100000]

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
        return instrument.reduction_runs.filter(run_number__in=self.run_number)

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

    def _verify_runs_exist_and_have_variable_value(self, variable_value):
        # Go to the runs list page
        RunsListPage(self.driver, self.instrument_name).launch()

        def make_run_url(run_number):
            return reverse("runs:summary",
                           kwargs={
                               "instrument_name": self.instrument_name,
                               "run_number": run_number,
                               "run_version": 1
                           })

        runs_list_page = RunsListPage(self.driver, self.instrument_name)
        for run in self.run_number:
            runs_list_page.launch()
            run_number_v1 = self.driver.find_element_by_css_selector(f'[href*="{make_run_url(run)}"]')
            assert run_number_v1.is_displayed()
            assert RunSummaryPage(self.driver, self.instrument_name, run,
                                  1).launch().variable1_field.get_attribute("value") == variable_value
            vars_for_run_v1 = InstrumentVariable.objects.filter(start_run=run)
            for var in vars_for_run_v1:
                assert var.value == variable_value

    def test_run_range_default_variable_value(self):
        assert not self.page.form_validation_message.is_displayed()
        expected_run = "99999-100000"
        self.page.run_range_field = expected_run
        self.page.submit_button.click()
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})
        assert expected_url in self.driver.current_url
        # wait until the message processing is complete before ending the test
        # otherwise the message handling can polute the DB state for the next test
        result = self.wait_for_result()
        assert len(result) == 4

        self._verify_runs_exist_and_have_variable_value("value2")

    def test_run_range_new_variable_value(self):
        expected_run = "99999-100000"
        self.page.run_range_field = expected_run
        new_value = "some_new_value"
        self.page.variable1_field = new_value
        self.page.submit_button.click()
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})
        assert expected_url in self.driver.current_url
        # wait until the message processing is complete before ending the test
        # otherwise the message handling can polute the DB state for the next test
        result = self.wait_for_result()
        assert len(result) == 4

        self._verify_runs_exist_and_have_variable_value(new_value)
