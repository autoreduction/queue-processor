# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the run summary page model
"""
from __future__ import annotations

from django.urls.base import reverse
from selenium.webdriver.remote.webelement import WebElement
from selenium_tests import configuration
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.rerun_form_mixin import RerunFormMixin
from selenium_tests.pages.component_mixins.tour_mixin import TourMixin
from selenium_tests.pages.page import Page


class RunSummaryPage(Page, RerunFormMixin, NavbarMixin, FooterMixin, TourMixin):
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

    def launch(self) -> RunSummaryPage:
        """
        Open the page with the webdriver
        :return: The RunSummaryPage object model
        """
        # Navigates to / first to force a login. Check the README and
        # the "index" view for more details
        self.driver.get(configuration.get_url())
        self.driver.get(self.url())
        return self

    @property
    def reduction_job_panel(self) -> WebElement:
        return self.driver.find_element_by_id("reduction_job_panel")

    @property
    def rerun_form(self) -> WebElement:
        """Finds and returns the rerun form on the page"""
        return self.driver.find_element_by_id("rerun_form")

    @property
    def toggle_button(self) -> WebElement:
        """
        Finds and returns the toggle button for toggling the form on the page.
        """
        return self.driver.find_element_by_id("toggle_form")

    @property
    def reset_to_initial_values(self) -> WebElement:
        """
        Finds and returns the "Reset to original script and values" button
        """
        return self.driver.find_element_by_id("resetValues")

    @property
    def reset_to_current_values(self) -> WebElement:
        """
        Finds and returns the "Reset to values in the current reduce_vars script" button
        """
        return self.driver.find_element_by_id("currentScript")
