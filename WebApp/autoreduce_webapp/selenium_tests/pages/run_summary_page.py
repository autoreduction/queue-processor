# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the run summary page model
"""
from django.urls.base import reverse
from selenium_tests import configuration
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.tour_mixin import TourMixin
from selenium_tests.pages.page import Page


class RunSummaryPage(Page, NavbarMixin, FooterMixin, TourMixin):
    """
    Page model class for run summary page
    """
    def __init__(self, driver, instrument, run_number, version):
        super().__init__(driver)
        self.instrument = instrument
        self.run_number = run_number
        self.version = version

    def url_path(self) -> str:
        """
        Return the current URL of the page.
        :return: (str) the url path
        """
        return reverse("runs:summary",
                       kwargs={
                           "instrument_name": self.instrument,
                           "run_number": self.run_number,
                           "run_version": self.version
                       })

    def launch(self):
        """
        Open the page with the webdriver
        :return: The RunSummaryPage object model
        """
        self.driver.get(configuration.get_url())
        self.driver.get(self.url())
        return self

    def is_rerun_form_visible(self) -> bool:
        """
        Check if the rerun form is visible on a page
        :return: (bool) True if form is visible False otherwise
        """
        return self.driver.find_element_by_id("rerun-form").is_displayed()
