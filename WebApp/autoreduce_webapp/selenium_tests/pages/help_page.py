# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the help summary page model
"""
from __future__ import annotations
from typing import List

from django.urls.base import reverse
from selenium.webdriver.remote.webelement import WebElement

from selenium_tests import configuration
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.page import Page


class HelpPage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for help page
    """

    def __init__(self, driver):
        super().__init__(driver)

    def url_path(self) -> str:
        """
        Return the current URL of the page.
        :return: (str) the url path
        """
        return reverse("help")

    def launch(self) -> HelpPage:
        """
        Open the page with the webdriver
        :return: (HelpPage) The HelpPage object model
        """
        # Navigates to / first to force a login. Check the README and
        # the "index" view for more details
        self.driver.get(configuration.get_url())
        self.driver.get(self.url())
        return self

    def get_sidenav_contents(self) -> List[WebElement]:
        """
        Get the contents of the collapsible sidebar
        :return: (List) A list of <li> WebElements in #sidebar-contents
        """
        return self.driver.find_element_by_id("sidenav-contents").find_elements_by_tag_name("li")

    def get_help_topics(self) -> List[WebElement]:
        """
        Get the help topics on the page
        :return: (List) A list of <section> WebElements in .help-topic
        """
        return self.driver.find_elements_by_class_name("help-topic")
