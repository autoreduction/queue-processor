# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the instrument summary page model
"""
from typing import List

from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium_tests import configuration
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.tour_mixin import TourMixin
from selenium_tests.pages.page import Page
from selenium_tests.pages.run_summary_page import RunSummaryPage


class RunsListPage(Page, NavbarMixin, FooterMixin, TourMixin):
    """
    Page model class for instrument summary page
    """
    def __init__(self, driver, instrument):
        super().__init__(driver)
        self.instrument = instrument

    def url_path(self):
        """
        Return the path section of the instrument url
        :return: (str) Path section of the page url
        """
        return reverse("runs:list", kwargs={"instrument": self.instrument})

    def launch(self):
        """
        Open the instrument summary page with the webdriver
        """
        self.driver.get(configuration.get_url())
        self.driver.get(self.url())
        return self

    def get_run_numbers_from_table(self) -> List[str]:
        """
        Get the list of run numbers visible on the current table of the instrument summary page
        :return: (List) List of strings of the run numbers of the current instrument summary page
        """
        return [run.text.split(" - ")[0] for run in self.driver.find_elements_by_class_name("run-num-links")]

    def click_run(self, run_number: int, version: int = 0) -> RunSummaryPage:
        """
        Click the run number link on the instrument summary table matching the given run number and
        version
        :param run_number: (int) the run number of the link to click
        :param version: (int) the version of the run to click
        :return: (RunSummaryPage) The page object of the opened run summary page.
        """
        runs = self.driver.find_elements_by_class_name("run-num-links")
        run_string = f"{run_number} - {version}" if version else f"{run_number}"
        for run in runs:
            if run.text == run_string:
                run.click()
                return RunSummaryPage(self.driver, self.instrument, run_number, version)
        raise NoSuchElementException

    def alert_message_text(self) -> str:
        """Get the the from the alert message"""
        return self.driver.find_element_by_id("alert_message").text.strip()
