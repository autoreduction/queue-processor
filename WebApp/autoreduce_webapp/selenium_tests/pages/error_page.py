# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the error page model
"""
from __future__ import annotations

from django.urls.base import reverse

from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.page import Page


class ErrorPage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for the error view
    """
    @staticmethod
    def url_path() -> str:
        """
        Return the current URL of the page. Overview will be used to test the error.
        :return: (str) the url path
        """
        return reverse("overview")  # /overview is used to test the error view

    def get_error_message(self) -> str:
        """
        Get the error message from the page
        :return: (str) The text in #error-message
        """
        return self.driver.find_element_by_id("error-message").text
