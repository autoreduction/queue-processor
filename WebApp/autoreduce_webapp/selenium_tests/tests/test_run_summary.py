# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the runs summary page
"""

import os
import tempfile
from unittest.mock import Mock, patch

from autoreduce_webapp.settings import STATIC_PATH
from django.urls import reverse
from reduction_viewer.models import ReductionRun
from selenium.webdriver.support.wait import WebDriverWait
from selenium_tests.pages.run_summary_page import RunSummaryPage
from selenium_tests.tests.base_tests import BaseTestCase, FooterTestMixin, NavbarTestMixin, \
    AccessibilityTestMixin
from systemtests.utils.data_archive import DataArchive


class TestRunSummaryPageNoArchive(NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin):
    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    accessibility_test_known_issues = {
        # https://github.com/ISISScientificComputing/autoreduce/issues/790
        "color-contrast": "*",
    }

    @classmethod
    def setUpClass(cls):
        """Set the instrument for all test cases"""
        super().setUpClass()
        cls.instrument_name = "TestInstrument"

    def setUp(self) -> None:
        """Set up RunSummaryPage before each test case"""
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
        assert self.page.run_description_text() == "Run description: This is the test run_description"


class TestRunSummaryPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the InstrumentSummary page when the Rerun form is NOT visible
    """

    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    @classmethod
    def setUpClass(cls):
        """Sets up Dataarchive with scripts and sets instrument for all test cases"""
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive = DataArchive([cls.instrument_name], 21, 21)
        cls.data_archive.create()
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                """standard_vars={"variable1":"test_variable_value_123"}""")

    @classmethod
    def tearDownClass(cls) -> None:
        """Destroys created data archive"""
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        """Sets up RunSummaryPage before each test case"""
        super().setUp()
        self.page = RunSummaryPage(self.driver, self.instrument_name, 99999, 0)
        self.page.launch()

    def test_reduction_job_panel_displayed(self):
        """Tests that the reduction job panel is showing the right things"""
        # only one run in the fixture, get it for assertions
        run = ReductionRun.objects.first()
        assert self.page.reduction_job_panel.is_displayed()
        assert self.page.run_description_text() == f"Run description: {run.run_description}"
        # because it's started_by: -1, determined in `started_by_id_to_name`
        assert self.page.started_by_text() == "Started by: Development team"
        assert self.page.status_text() == "Status: Processing"
        assert self.page.instrument_text() == f"Instrument: {run.instrument.name}"
        assert self.page.rb_number_text() == f"RB Number: {run.experiment.reference_number}"
        assert self.page.last_updated_text() == "Last Updated: 19 Oct 2020, 6:35 p.m."
        assert self.page.reduction_host_text() == "Host: test-host-123"

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

        WebDriverWait(self.driver, 10).until(lambda _: labels[0].text == "Re-run description")
        WebDriverWait(self.driver, 10).until(lambda _: labels[1].text == "variable1")

    def test_back_to_instruments_goes_back(self):
        """
        Test: Clicking back goes back to the instrument
        """
        back = self.page.cancel_button
        assert back.is_displayed()
        assert back.text == f"Back to {self.instrument_name} runs"
        back.click()
        assert reverse("runs:list", kwargs={"instrument": self.instrument_name}) in self.driver.current_url


class TestRunSummaryPagePlots(BaseTestCase):
    """
    Test cases for the InstrumentSummary page when the Rerun form is NOT visible
    """

    fixtures = BaseTestCase.fixtures + ["one_run_plot"]

    def setUp(self) -> None:
        """
        Set up the instrument name and page
        """
        super().setUp()
        self.instrument_name = "TestInstrument"

        self.page = RunSummaryPage(self.driver, self.instrument_name, 99999, 0)

    def test_local_plot_files(self):
        """
        Test: Local plot files are fetched and shown
        """
        plot_files = [
            tempfile.NamedTemporaryFile(prefix="data_", suffix=".png", dir=f"{STATIC_PATH}/graphs/"),
            tempfile.NamedTemporaryFile(prefix="data_", suffix=".png", dir=f"{STATIC_PATH}/graphs/")
        ]
        self.page.launch()

        # 1 is the logo, the other 2 are the plots
        images = self.page.images()
        assert len(images) == 3
        for img in images[1:]:
            alt_text = img.get_attribute("alt")
            assert "Plot image stored at" in alt_text
            assert any(os.path.basename(f.name) in alt_text for f in plot_files)

    @patch("plotting.plot_handler.SFTPClient")
    def test_remote_plot_files(self, sftp_client: Mock):
        """
        Test: Remote plot files are fetched and shown
        """
        plot_files = [
            "file1.png",
            "file2.png",
            "file3.png",
            "file4.png",
        ]
        sftp_client.return_value.get_filenames.return_value = plot_files

        self.page.launch()
        # 1 is the logo, the other 4 are the plots
        images = self.page.images()
        assert len(images) == 5
        for img in images[1:]:
            alt_text = img.get_attribute("alt")
            assert "Plot image stored at" in alt_text
            assert any(os.path.basename(f) in alt_text for f in plot_files)
