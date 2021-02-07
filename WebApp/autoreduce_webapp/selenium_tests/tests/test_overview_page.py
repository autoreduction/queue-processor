# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the overview page
"""

from selenium_tests.pages.instrument_summary_page import InstrumentSummaryPage
from selenium_tests.pages.overview_page import OverviewPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin


class TestOverviewPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the overview page
    """
    fixtures = BaseTestCase.fixtures + ["test_overview_page"]

    def setUp(self) -> None:
        """
        Sets up the OverviewPage object
        """
        super().setUp()
        self.page = OverviewPage(self.driver)


    def test_correct_instruments_visible(self):
        """
        Tests: Correct instruments displayed
        When: VALID_INSTRUMENTS is viewable from test environment
        """
        actual_instruments = self.page\
            .launch() \
            .get_instruments_from_buttons()
        expected_instruments = ["ActiveInstrument", "InactiveInstrument", "PausedInstrument"]
        self.assertTrue(set(expected_instruments).issubset(actual_instruments))

    def test_instrument_buttons_go_to_instrument_summary_pages(self):
        """
        Tests: Instrument overviewpage is navigated to
        When: Instrument button is clicked
        """
        instruments = self.page \
            .launch() \
            .get_instruments_from_buttons()
        for instrument in instruments:
            self.page.click_instrument(instrument)
            self.assertTrue(self.driver.current_url.endswith(InstrumentSummaryPage.url_path() % instrument))
            self.page.launch()

    def test_tour(self):
        """
        Tests: Tour run through on overview page
        """
        self.page \
            .launch() \
            .start_tour()
        self.assertTrue(self.page.is_tour_visible())
        self.assertFalse(self.page.is_tour_previous_button_enabled())
        self.page.next_tour_step()
        self.assertTrue(self.page.is_tour_visible())
        self.page.next_tour_step()
        self.assertTrue(self.page.is_tour_visible())
        self.assertFalse(self.page.is_tour_next_button_enabled())
        self.page.end_tour()
        self.assertTrue(self.page.is_tour_hidden())
