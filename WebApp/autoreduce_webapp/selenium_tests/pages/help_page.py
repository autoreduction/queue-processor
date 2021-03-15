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

    def _get_sidenav_contents_elements(self) -> List[WebElement]:
        """
        Get the contents of the sidenav
        :return: (List) A list of <li> WebElements in #sidenav-contents
        """
        return self.driver.find_elements_by_xpath("//ul[@id='sidenav-contents']/li")

    def get_sidenav_contents(self) -> List[str]:
        """
        Get the contents of the sidenav as a list of strings.
        Should be run post topic JS link generation.
        :return: (List) A list of strings inside of each <a> element
        """
        return [x.find_element_by_tag_name("a").text.strip() for x in self._get_sidenav_contents_elements()]

    def get_help_topic_elements(self) -> List[WebElement]:
        """
        Get the help topics
        :return: (List) A list of <section> WebElements in .help-topic
        """
        return self.driver.find_elements_by_class_name("help-topic")

    def get_help_topic_headers(self) -> List[str]:
        """
        Get the headers of the help topics.
        Should be run post JS topic link generation.
        :return (List) A list of topic headers
        """
        return [x.find_element_by_xpath("./div[@class='panel-heading']/h3/a").text.strip() for x in self.get_help_topic_elements()]

    def _get_category_filter_elements(self) -> List[WebElement]:
        """
        Get the filter elements in #category-filter
        :return: (List) A list of filter elements
        """
        return self.driver.find_elements_by_xpath("//div[id='category-filter']/label")

    def get_topic_categories(self) -> List[str]:
        """
        Get the topic categories from the category filter
        :return: (List) A list of categories
        """
        return [x.text.strip().lower() for x in self._get_category_filter_elements() if x != "All"]

    def get_each_help_topic_category(self) -> List[str]:
        """
        Get each data-category from each topic
        :return: (List) A list of categories from each topic
        """
        return [x.get_attribute("data-category") for x in self.get_help_topic_elements()]

    def get_each_help_topic_content(self):
        """
        Get each content text for each topic
        :return: (List) A list of topic contents
        """
        return [x.find_element_by_class_name("panel-body").text for x in self.get_help_topic_elements()]
