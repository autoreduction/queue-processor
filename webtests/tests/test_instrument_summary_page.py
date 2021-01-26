# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the instrument summary page
"""

from webtests.pages.instrument_summary_page import InstrumentSummaryPage
from webtests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin


class TestInstrumentSummaryPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the InstrumentSummary page
    """

    def setUp(self) -> None:
        """
        Sets up the InstrumentSummaryPage object
        """
        super().setUp()
        self.page = InstrumentSummaryPage(self.driver, "WISH")

    def test_reduction_run_displayed(self):
        """
        Test: Reduction run is displayed
        When: The run exists in the database
        """
        runs = self.page.launch() \
            .get_run_numbers_from_table()
        self.assertIn("99999", runs)
