# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing the NavbarMixin
"""
from typing import List

from selenium.webdriver.remote.webelement import WebElement


class NavbarMixin:
    """
    NavbarMixin adds functionality of the navbar to a page when inherited
    """
    NAVBAR_CLASS = "navbar"
    LOGO_CLASS = "navbar-brand"
    LINKS_ID = "navbar_links"
    ALL_INSTRUMENTS_LINK_XPATH = ".//a[contains(text(), 'All Instruments')]"
    JOB_QUEUE_XPATH = ".//a[contains(text(), 'Job Queue')]"
    FAILED_JOBS_XPATH = ".//a[contains(text(), 'Failed Jobs')]"
    GRAPHS_XPATH = ".//a[contains(text(), 'Graphs')]"
    HELP_XPATH = ".//a[contains(text(), 'Help')]"

    def click_navbar_logo(self):
        """
        Click the brand logo in the navbar and return the current page
        """
        self.driver.find_element_by_class_name(self.NAVBAR_CLASS).click()
        return self

    def click_navbar_all_instruments(self):
        """
        Click the all instruments link in the navbar
        """
        self.driver.find_element_by_xpath(self.ALL_INSTRUMENTS_LINK_XPATH).click()

    def click_navbar_job_queue(self):
        """
        Click the job queue link in the navbar
        """
        self.driver.find_element_by_xpath(self.JOB_QUEUE_XPATH).click()

    def click_navbar_failed_jobs(self):
        """
        Click the failed jobs link in the navbar
        """
        self.driver.find_element_by_xpath(self.FAILED_JOBS_XPATH).click()

    def click_navbar_graphs(self):
        """
        Click the graphs link in the navbar
        """
        self.driver.find_element_by_xpath(self.GRAPHS_XPATH).click()

    def click_navbar_help(self):
        """
        Click the help link in the navbar
        """
        self.driver.find_element_by_xpath(self.HELP_XPATH).click()

    def _get_navbar(self) -> WebElement:
        return self.driver.find_element_by_class_name(self.NAVBAR_CLASS)

    def _get_logo(self) -> WebElement:
        return self.driver.find_element_by_class_name(self.LOGO_CLASS)

    def _get_navbar_links(self) -> WebElement:
        return self.driver.find_element_by_id(self.LINKS_ID)

    def is_navbar_logo_visible(self) -> bool:
        """
        Check if the brand logo is visible in the navbar
        :return: (bool) True if logo is visible, otherwise False
        """
        return self._get_logo().is_displayed()

    def is_navbar_visible(self) -> bool:
        """
        Check if the navbar is visible on a page
        :return: (bool) True if navbar is visible, otherwise False
        """
        return self._get_navbar().is_displayed()

    def is_navbar_links_visible(self) -> bool:
        """
        Check if the navbar links are visible
        :return: (bool) True if links are visible, otherwise False
        """
        return self._get_navbar_links().is_displayed()

    def get_notification_messages(self) -> List[str]:
        """
        Get the notification messages on the page.
        :return: The text of the notifications messages
        """
        return [notification.text for notification in self.driver.find_elements_by_class_name("notification-message")]
