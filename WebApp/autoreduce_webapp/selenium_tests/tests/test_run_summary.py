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
from reduction_viewer.models import ReductionRun
from selenium_tests.pages.run_summary_page import RunSummaryPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin

from systemtests.utils.data_archive import DataArchive


class TestRunSummaryPageNoArchive(BaseTestCase):
    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instrument_name = "TestInstrument"

    def setUp(self) -> None:
        super().setUp()
        self.page = RunSummaryPage(self.driver, self.instrument_name, 99999, 0)
        self.page.launch()

    def test_opening_run_summary_without_reduce_vars(self):
        """
        Test that opening the run summary without a reduce_vars present for the instrument
        will not show the "Reset to current" buttons as there is no current values!
        """
        # the reset to current values should not be visible
        assert self.page.warning_message.is_displayed()
        assert self.page.warning_message.text == ("The reduce_vars.py script is missing for this instrument."
                                                  " Please create it before being able to submit re-runs.")

    def test_opening_run_summary_without_run_variables(self):
        """
        Test that opening the run summary without a reduce_vars present for the instrument
        will not show the "Reset to current" buttons as there is no current values!
        """
        # Delete the variables, and re-open the page
        ReductionRun.objects.get(pk=1).run_variables.all().delete()
        self.page.launch()
        # the reset to current values should not be visible
        assert self.page.warning_message.is_displayed()
        assert self.page.warning_message.text == "No variables found for this run."


class TestRunSummaryPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the InstrumentSummary page when the Rerun form is NOT visible
    """

    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive = DataArchive([cls.instrument_name], 21, 21)
        cls.data_archive.create()
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                """standard_vars={"variable1":"test_variable_value_123"}""")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.page = RunSummaryPage(self.driver, self.instrument_name, 99999, 0)
        self.page.launch()

    def test_reduction_job_panel_displayed(self):
        """Tests that the reduction job panel is showing the right things"""
        rjp = self.page.reduction_job_panel
        assert rjp.is_displayed()

    def test_reduction_job_panel_reset_to_values_first_used_for_run(self):
        """Test that the button to reset the variables to the values first used for the run works"""
        self.page.toggle_button.click()
        self.page.variable1_field = "the new value in the field"

        self.page.reset_to_initial_values.click()

        # need to re-query the driver because resetting replaces the elements
        assert self.page.variable1_field.get_attribute("value") == "value1"

    def test_reduction_job_panel_reset_to_current_reduce_vars(self):
        """Test that the button to reset the variables to the values from the reduce_vars script works"""
        self.page.toggle_button.click()
        self.page.variable1_field = "the new value in the field"

        self.page.reset_to_current_values.click()

        # need to re-query the driver because resetting replaces the elements
        assert self.page.variable1_field.get_attribute("value") == "test_variable_value_123"

    def test_rerun_form(self):
        """
        Test: Rerun form shows contents from Variable in database (from the fixture) and not reduce_vars.py
        """
        rerun_form = self.page.rerun_form
        assert not rerun_form.is_displayed()
        self.page.toggle_button.click()
        assert rerun_form.is_displayed()
        assert rerun_form.find_element_by_id("var-standard-variable1").get_attribute("value") == "value1"
        labels = rerun_form.find_elements_by_tag_name("label")

        assert labels[0].text == "Re-run description"
        assert labels[1].text == "variable1"

    def test_back_to_instruments_goes_back(self):
        """
        Test: Clicking back goes back to the instrument
        """
        back = self.page.cancel_button
        assert back.is_displayed()
        assert back.text == f"Back to {self.instrument_name} runs"
        back.click()
        assert reverse("runs:list", kwargs={"instrument": self.instrument_name}) in self.driver.current_url
