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
from selenium.webdriver.remote.webelement import WebElement
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.rerun_form_mixin import RerunFormMixin
from selenium_tests.pages.component_mixins.tour_mixin import TourMixin
from selenium_tests.pages.page import Page


class RerunJobsPage(Page, RerunFormMixin, NavbarMixin, FooterMixin, TourMixin):
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

    @property
    def form_validation_message(self) -> WebElement:
        """Finds and returns the form validation message"""
        return self.driver.find_element_by_id("form_validation_message")

    @property
    def form(self) -> WebElement:
        """Finds and returns the rerun form on the page"""
        return self.driver.find_element_by_id("submit_jobs")

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
        self._set_field(self.run_range_field, value)

    @property
    def reset_to_current_values(self) -> WebElement:
        """
        Finds and returns the "Reset to values in the current reduce_vars script" button
        """
        return self.driver.find_element_by_id("currentScript")

    @property
    def error_container(self) -> WebElement:
        """
        Returns the container of the error message
        """
        return self.driver.find_element_by_id("error_container")

    def error_message_text(self) -> str:
        """
        Returns the text shown in the error message
        """
        return self.driver.find_element_by_id("error_message").text
