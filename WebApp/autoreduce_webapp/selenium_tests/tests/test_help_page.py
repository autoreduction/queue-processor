# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import re

from selenium_tests.pages.help_page import HelpPage
from selenium_tests.tests.base_tests import (NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin)
from selenium.webdriver.support.wait import WebDriverWait


class TestHelpPage(NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin):
    """
    Test cases for the help page
    """
    accessibility_test_known_issues = {"color-contrast": "*"}

    def setUp(self) -> None:
        """
        Sets up the HelpPage object
        """
        super().setUp()
        self.page = HelpPage(self.driver)
        self.page.launch()

    def test_at_least_one_topic_exists(self):
        """
        Test that at least one help topic is on the page
        """
        self.assertNotEqual(0, len(self.page.get_help_topic_elements()))

    def test_all_sidebar_content_generated(self):
        """
        Test that the sidebar lists all the help topic headers
        """
        WebDriverWait(self.driver,
                      10).until(lambda _: self.page.get_sidenav_contents() == self.page.get_each_help_topic_header())

    def test_all_help_topics_have_a_valid_category(self):
        """
        Test that all topics have a valid data-category="..."
        """
        WebDriverWait(self.driver, 10).until(lambda _: set(self.page.get_each_help_topic_category()) == set(
            self.page.get_available_help_topic_categories()))

    def test_all_help_topics_have_content(self):
        """
        Test that all help topic elements have content in .panel-body
        """
        WebDriverWait(self.driver,
                      10).until(lambda _: "" not in [x.strip() for x in self.page.get_each_help_topic_content()])

    def test_filter_help_topics_by_category(self):
        """
        Test that the category filter filters out help topics based on the category or "all"
        """
        for category_filter in self.page.get_help_topic_filters():
            self.page.click_category_filter(category_filter)
            self.assertEqual(self.page.get_visible_help_topic_elements(), [
                x for x in self.page.get_help_topic_elements()
                if x.get_attribute("data-category") == category_filter or category_filter == "all"
            ])

    def test_filter_topics_by_fuzzy_search(self):
        """
        Test that the search bar searches help topics correctly using the first word of the header and content.
        """
        # Search for first word in content of first help topic with filter "all"
        self.page.filter_help_topics_by_search_term(self.page.get_each_help_topic_content()[0].split()[0])
        self.assertIn(self.page.get_help_topic_elements()[0], self.page.get_visible_help_topic_elements())

        self.page.clear_search_box()
        WebDriverWait(self.driver, 10).until(lambda _: self.page.get_each_help_topic_content()[0] != "")

        # Search for first word in header of first help topic with filter "all"
        self.page.filter_help_topics_by_search_term(self.page.get_each_help_topic_header()[0].split()[0])
        self.assertIn(self.page.get_help_topic_elements()[0], self.page.get_visible_help_topic_elements())

        self.page.clear_search_box()
        WebDriverWait(self.driver, 10).until(lambda _: self.page.get_each_help_topic_content()[0] != "")

        # Search for a word not in the first topic with filter "all"
        self.page.filter_help_topics_by_search_term("veryrandomstringthatshouldnotbeintopic")
        self.assertNotIn(self.page.get_help_topic_elements()[0], self.page.get_visible_help_topic_elements())

        self.page.clear_search_box()
        WebDriverWait(self.driver, 10).until(lambda _: self.page.get_each_help_topic_content()[0] != "")

        # Search for first word in content of first help topic with filter that is the same as the first topic category
        self.page.filter_help_topics_by_search_term(self.page.get_each_help_topic_content()[0].split()[0])
        self.page.click_category_filter(self.page.get_each_help_topic_category()[0])
        self.assertIn(self.page.get_help_topic_elements()[0], self.page.get_visible_help_topic_elements())

        self.page.clear_search_box()
        WebDriverWait(self.driver, 10).until(lambda _: self.page.get_each_help_topic_content()[0] != "")

        # Search for first word in content of first help topic with filter that is different to the first topic category
        self.page.filter_help_topics_by_search_term(self.page.get_each_help_topic_content()[0].split()[0])
        categories = self.page.get_available_help_topic_categories()
        categories.remove(self.page.get_each_help_topic_category()[0])
        self.page.click_category_filter(categories[0])
        self.assertNotIn(self.page.get_help_topic_elements()[0], self.page.get_visible_help_topic_elements())

    def test_help_topic_link_generation(self):
        """
        Test that help topic header links are correctly constructed
        """
        def to_link_text(text):
            return re.sub("[^A-Za-z0-9\\s]+", "", text).replace(" ", "-").lower()

        for link_element in self.page.get_help_topic_header_link_elements():
            self.assertEqual(link_element.get_attribute("href").split("#", 1)[1], to_link_text(link_element.text))
