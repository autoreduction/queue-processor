# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from django.urls import reverse
from instrument.models import InstrumentVariable
from selenium_tests.pages.rerun_jobs_page import RerunJobsPage
from selenium_tests.pages.run_summary_page import RunSummaryPage
from selenium_tests.pages.runs_list_page import RunsListPage
from selenium_tests.tests.base_tests import (NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin)
from selenium_tests.utils import submit_and_wait_for_result

from WebApp.autoreduce_webapp.selenium_tests.utils import setup_external_services


class TestRerunJobsRangePageIntegration(NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin):
    fixtures = BaseTestCase.fixtures + ["two_runs"]
    accessibility_test_known_issues = {
        "color-contrast": "*",  # https://github.com/ISISScientificComputing/autoreduce/issues/790
        "duplicate-id-aria": "input",
        # https://github.com/ISISScientificComputing/autoreduce/issues/1267
    }

    @classmethod
    def setUpClass(cls):
        """Starts all external services"""
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive, cls.database_client, cls.queue_client, cls.listener = setup_external_services(
            cls.instrument_name, 21, 21)
        cls.data_archive.add_reduction_script(cls.instrument_name, """print('some text')""")
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                """standard_vars={"variable1":"test_variable_value_123"}""")
        cls.rb_number = 1234567
        cls.run_number = [99999, 100000]

    @classmethod
    def tearDownClass(cls) -> None:
        """Stops all external services"""
        cls.queue_client.disconnect()
        cls.database_client.disconnect()
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        """Sets up and launches RerunJobsPage before each test case"""
        super().setUp()
        self.page = RerunJobsPage(self.driver, self.instrument_name)
        self.page.launch()

    def _verify_runs_exist_and_have_variable_value(self, variable_value):
        """
        Verifies that the run with version 1 exists and has the expected value
        """
        def make_run_url(run_number):
            """Constructs the url of the run summary with a django reverse"""
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
        """
        Test setting a run range with the default variable value
        """
        assert not self.page.form_validation_message.is_displayed()
        expected_run = "99999-100000"
        self.page.run_range_field = expected_run
        result = submit_and_wait_for_result(self)
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})
        assert expected_url in self.driver.current_url
        # wait until the message processing is complete before ending the test
        # otherwise the message handling can pollute the DB state for the next test
        assert len(result) == 4

        self._verify_runs_exist_and_have_variable_value("value2")

    def test_run_range_new_variable_value(self):
        """
        Test setting a run range with a new variable value
        """
        expected_run = "99999-100000"
        self.page.run_range_field = expected_run
        new_value = "some_new_value"
        self.page.variable1_field = new_value
        result = submit_and_wait_for_result(self)
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})
        assert expected_url in self.driver.current_url
        # wait until the message processing is complete before ending the test
        # otherwise the message handling can pollute the DB state for the next test
        assert len(result) == 4

        self._verify_runs_exist_and_have_variable_value(new_value)
