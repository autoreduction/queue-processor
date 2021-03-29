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

from typing import List

from django.urls.base import reverse
from selenium.webdriver.remote.webelement import WebElement
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.rerun_form_mixin import \
    RerunFormMixin
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

    @property
    def reduction_job_panel(self) -> WebElement:
        """Finds the run summary panel on the page."""
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

    @property
    def warning_message(self) -> WebElement:
        """
        Finds and returns the "warning_message" box
        """
        return self.driver.find_element_by_id("warning_message")

    def run_description_text(self) -> str:
        """
        Finds and returns the text of the run_description field
        """
        return self.driver.find_element_by_id("run_description").text

    def started_by_text(self) -> str:
        """
        Finds and returns the text of the started_by field
        """
        return self.driver.find_element_by_id("started_by").text

    def status_text(self) -> str:
        """
        Finds and returns the text of the status field
        """
        return self.driver.find_element_by_id("status").text

    def instrument_text(self) -> str:
        """
        Finds and returns the text of the instrument field
        """
        return self.driver.find_element_by_id("instrument").text

    def rb_number_text(self) -> str:
        """
        Finds and returns the text of the rb_number field
        """
        return self.driver.find_element_by_id("rb_number").text

    def last_updated_text(self) -> str:
        """
        Finds and returns the text of the last_updated field
        """
        return self.driver.find_element_by_id("last_updated").text

    def reduction_host_text(self) -> WebElement:
        """
        Returns the reduction host text
        """
        return self.driver.find_element_by_id("reduction_host").text

    def images(self) -> List[WebElement]:
        """
        Returns all image elements on the page.
        """
        return self.driver.find_elements_by_tag_name("img")
