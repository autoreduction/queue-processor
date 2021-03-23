# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the runs summary page
"""

from django.urls import reverse
from selenium_tests.pages.run_summary_page import RunSummaryPage
from selenium_tests.tests.base_tests import (BaseTestCase, FooterTestMixin, NavbarTestMixin)
from selenium_tests.utils import submit_and_wait_for_result

from WebApp.autoreduce_webapp.selenium_tests.utils import setup_external_services


class TestRunSummaryPageIntegration(BaseTestCase, FooterTestMixin, NavbarTestMixin):
    """
    Test cases for the InstrumentSummary page when the Rerun form is NOT visible
    """

    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    @classmethod
    def setUpClass(cls):
        """ Start all external services """
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.rb_number = 1234567
        cls.run_number = 99999
        cls.data_archive, cls.database_client, cls.queue_client, cls.listener = setup_external_services(
            cls.instrument_name, 21, 21)
        cls.data_archive.add_reduction_script(cls.instrument_name, """print('some text')""")
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                """standard_vars={"variable1":"test_variable_value_123"}""")

    @classmethod
    def tearDownClass(cls) -> None:
        """Stop all external services"""
        cls.queue_client.disconnect()
        cls.database_client.disconnect()
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        """Sets up the RunSummaryPage and shows the rerun panel before each test case"""
        super().setUp()
        self.page = RunSummaryPage(self.driver, self.instrument_name, 99999, 0)
        self.page.launch()
        # clicks the toggle to show the rerun panel, otherwise the buttons in the form are non interactive
        self.page.toggle_button.click()

    def test_submit_rerun_same_variables(self):
        """
        Test: Just opening the submit page and clicking rerun
        """
        result = submit_and_wait_for_result(self)
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

        result = submit_and_wait_for_result(self)
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
        result = submit_and_wait_for_result(self)
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
        result = submit_and_wait_for_result(self)

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
        result = submit_and_wait_for_result(self)
        expected_url = reverse("run_confirmation", kwargs={"instrument": self.instrument_name})
        assert expected_url in self.driver.current_url
        # wait until the message processing is complete before ending the test
        # otherwise the message handling can pollute the DB state for the next test
        assert len(result) == 2
        # check that the error is because of missing Mantid
        # if this fails then something else in the reduction caused an error instead!
        assert "Mantid" in result[1].admin_log
