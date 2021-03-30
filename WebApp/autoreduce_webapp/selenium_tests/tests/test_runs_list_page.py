# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the runs summary page
"""

from selenium_tests.pages.runs_list_page import RunsListPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin, \
    AccessibilityTestMixin
from systemtests.utils.data_archive import DataArchive


class TestRunsListPage(NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin):
    """
    Test cases for the InstrumentSummary page
    """

    fixtures = BaseTestCase.fixtures + ["test_runs_list_page"]

    def setUp(self) -> None:
        """
        Sets up the InstrumentSummaryPage object
        """
        super().setUp()
        self.instrument_name = "TestInstrument"
        self.page = RunsListPage(self.driver, self.instrument_name)

    def test_reduction_run_displayed(self):
        """
        Test: Reduction run is displayed
        When: The run exists in the database
        """
        runs = self.page.launch().get_run_numbers_from_table()
        assert "99999" in runs

    def test_alert_message_when_missing_reduce_vars(self):
        """
        Test that the correct message is shown when the reduce_vars.py file is missing
        """
        self.page.launch()
        expected = "The buttons above have been disabled because reduce_vars.py is missing for this instrument."
        assert self.page.alert_message_text() == expected

    def test_alert_message_when_reduce_vars_has_error(self):
        """
        Test that the correct message is shown when the reduce_vars.py has an error in it
        """
        data_archive = DataArchive([self.instrument_name], 21, 21)
        data_archive.create()

        # add a reduce_vars script with a syntax error -> a missing " after value1
        data_archive.add_reduce_vars_script(self.instrument_name, """standard_vars={"variable1":"value1}""")

        self.page.launch()
        expected = "The buttons above have been disabled because reduce_vars.py has an import or syntax error."
        assert self.page.alert_message_text() == expected

        data_archive.delete()
