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

from django.urls.base import reverse
from selenium_tests import configuration
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.rerun_form_mixin import \
    RerunFormMixin
from selenium_tests.pages.page import Page


class HelpPage(Page, RerunFormMixin, NavbarMixin, FooterMixin):
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
