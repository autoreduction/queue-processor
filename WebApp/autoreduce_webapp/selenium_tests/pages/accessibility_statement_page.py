# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the accessibility statement page model
"""
from __future__ import annotations

from django.urls.base import reverse
from selenium.webdriver.remote.webelement import WebElement

from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.page import Page


class AccessibilityStatementPage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for accessibility statement page
    """
    def __init__(self, driver):
        super().__init__(driver)

    def url_path(self) -> str:
        """
        Return the current URL of the page.
        :return: (str) the url path
        """
        return reverse("accessibility_statement")

    def get_accessibility_statement_contents_element(self) -> WebElement:
        """
        Get the <div> #accessibility-statement-contents
        :return: (WebElement) The element #accessibility-statement-contents
        """
        return self.driver.find_element_by_id("accessibility-statement-contents")
