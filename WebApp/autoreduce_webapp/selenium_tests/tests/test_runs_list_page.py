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
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin


class TestRunsListPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the InstrumentSummary page
    """

    fixtures = BaseTestCase.fixtures + ["test_instrument_summary_page"]

    def setUp(self) -> None:
        """
        Sets up the InstrumentSummaryPage object
        """
        super().setUp()
        self.page = RunsListPage(self.driver, "TestInstrument")

    def test_reduction_run_displayed(self):
        """
        Test: Reduction run is displayed
        When: The run exists in the database
        """
        runs = self.page.launch().get_run_numbers_from_table()
        self.assertIn("99999", runs)
