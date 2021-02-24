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
from selenium_tests.pages.component_mixins.tour_mixin import TourMixin
from selenium_tests.pages.page import Page


class RerunJobsPage(Page, NavbarMixin, FooterMixin, TourMixin):
    """
    Page model class for run summary page
    """
    def __init__(self, driver, instrument):
        super().__init__(driver)
        self.instrument = instrument

    def url_path(self) -> str:
        """
        Return the current URL of the page.
        :return: (str) the url path
        """
        return reverse("instrument:submit_runs", kwargs={
            "instrument": self.instrument,
        })

    def launch(self) -> RerunJobsPage:
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
    def form_validation_message(self) -> WebElement:
        return self.driver.find_element_by_id("form_validation_message")

    @property
    def form(self) -> WebElement:
        """Finds and returns the rerun form on the page"""
        return self.driver.find_element_by_id("submit_jobs")

    @property
    def submit_button(self) -> WebElement:
        """
        Finds and returns the back button for toggling the form on the page.
        """
        return self.driver.find_element_by_id("variableSubmit")

    @property
    def run_range_field(self) -> WebElement:
        """
        Finds and returns the back button for toggling the form on the page.
        """
        return self.driver.find_element_by_id("run_range")

    @run_range_field.setter
    def run_range_field(self, value) -> None:
        """
        Finds and returns the back button for toggling the form on the page.
        """
        var_field = self.run_range_field
        var_field.clear()
        new_value = value
        var_field.send_keys(new_value)

    @property
    def cancel_button(self) -> WebElement:
        """
        Finds and returns the back button for toggling the form on the page.
        """
        return self.driver.find_element_by_id("cancel")

    @property
    def reset_to_current_values(self) -> WebElement:
        """
        Finds and returns the "Reset to values in the current reduce_vars script" button
        """
        return self.driver.find_element_by_id("currentScript")

    @property
    def variable1_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable1")

    @variable1_field.setter
    def variable1_field(self, value):
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        var_field = self.variable1_field
        var_field.clear()
        new_value = value
        var_field.send_keys(new_value)
