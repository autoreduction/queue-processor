# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the overview page
"""

from selenium_tests.pages.overview_page import OverviewPage
from selenium_tests.tests.base_tests import (NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin)


class TestOverviewPage(NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin):
    """
    Test cases for the overview page
    """
    fixtures = BaseTestCase.fixtures + ["test_overview_page"]

    accessibility_test_known_issues = {
        # https://github.com/ISISScientificComputing/autoreduce/issues/790
        "color-contrast": "*",
    }  # pylint: disable=duplicate-code

    def setUp(self) -> None:
        """
        Sets up the OverviewPage object
        """
        super().setUp()
        self.page = OverviewPage(self.driver)

    def test_correct_instruments_visible(self):
        """
        Tests: Correct instruments displayed
        """
        actual_instruments = self.page.launch().get_instruments_from_buttons()
        expected_instruments = {"ActiveInstrument", "InactiveInstrument", "PausedInstrument"}
        self.assertTrue(expected_instruments.issubset(actual_instruments))

    def test_instrument_buttons_go_to_instrument_summary_pages(self):
        """
        Tests: Instrument overviewpage is navigated to
        When: Instrument button is clicked
        """
        instruments = self.page.launch().get_instruments_from_buttons()
        for instrument in instruments:
            instrument_page = self.page.click_instrument(instrument)
            self.assertTrue(self.driver.current_url.endswith(instrument_page.url_path()))
            self.page.launch()

    def test_tour(self):
        """
        Tests: Tour run through on overview page
        """
        self.page.launch().start_tour()
        self.assertTrue(self.page.is_tour_visible())
        self.assertFalse(self.page.is_tour_previous_button_enabled())
        self.page.next_tour_step()
        self.assertTrue(self.page.is_tour_visible())
        self.page.next_tour_step()
        self.assertTrue(self.page.is_tour_visible())
        self.assertFalse(self.page.is_tour_next_button_enabled())
        self.page.end_tour()
        self.assertTrue(self.page.is_tour_hidden())
