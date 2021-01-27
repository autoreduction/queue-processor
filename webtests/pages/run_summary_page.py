# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the run summary page model
"""
from webtests import configuration
from webtests.pages.component_mixins.footer_mixin import FooterMixin
from webtests.pages.component_mixins.navbar_mixin import NavbarMixin
from webtests.pages.component_mixins.tour_mixin import TourMixin
from webtests.pages.page import Page


class RunSummaryPage(Page, NavbarMixin, FooterMixin, TourMixin):
    """
    Page model class for run summary page
    """

    def __init__(self, driver, instrument, run_number, version):
        super().__init__(driver)
        self.instrument = instrument
        self.run_number = run_number
        self.version = version

    @staticmethod
    def url_path():
        """
        Return the lazy formatted url path in the form /runs/<instrument>/<run_number>/<version>/
        :return: (str) lazy formatted url path e.g. /runs/%s/%s/%s/
        """
        return "/runs/%s/%s/%s/"

    def launch(self):
        """
        Open the page with the webdriver
        :return: The RunSummaryPage object model
        """
        self.driver.get(configuration.get_url()) # Add note to readme about the login hack with the double get
        self.driver.get(RunSummaryPage.url() % (self.instrument, self.run_number, self.version))
        return self

    def is_rerun_form_visible(self) -> bool:
        """
        Check if the rerun form is visible on a page
        :return: (bool) True if form is visible False otherwise
        """
        return self.driver.find_element_by_id("rerun-form").is_displayed()
