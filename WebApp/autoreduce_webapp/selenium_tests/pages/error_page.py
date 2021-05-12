# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the error page model
"""
from django.urls.base import reverse

from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.page import Page
from selenium_tests import configuration


class ErrorPage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for the error view
    """
    def __init__(self, driver):
        super().__init__(driver)
        self.fake_token = "r07v2h39q453928"

    @staticmethod
    def url_path() -> str:
        """
        This needs to be overriden because the basemethod is abstract, but it isn't used
        because the launch method is overriden here too.

        :return: (str) the url path
        """
        return reverse("overview")

    def get_error_message(self) -> str:
        """
        Get the error message from the page
        :return: (str) The text in #error-message
        """
        return self.driver.find_element_by_id("error-message").text

    def launch_with_session(self):
        """
        Navigate the webdriver to this page.

        This overrides the default launch in order to provide a testing `sessionid` parameter.

        :return: The page object
        """
        self.driver.get(f"{configuration.get_url()}?sessionid={self.fake_token}")
        return self
