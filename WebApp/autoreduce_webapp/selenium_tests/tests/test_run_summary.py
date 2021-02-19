# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the runs summary page
"""

from selenium_tests.pages.run_summary_page import RunSummaryPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin


class TestRunSummaryPage(BaseTestCase):
    """
    Test cases for the InstrumentSummary page
    """

    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    def setUp(self) -> None:
        """
        Sets up the InstrumentSummaryPage object
        """
        super().setUp()
        self.page = RunSummaryPage(self.driver, "TestInstrument", 99999, 0)

    def test_reduction_run_displayed(self):
        """
        Test: Reduction run is displayed
        When: The run exists in the database
        """
        assert self.page.launch().is_rerun_form_visible()
