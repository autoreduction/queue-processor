import re

from selenium_tests.pages.help_page import HelpPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, \
    FooterTestMixin
from selenium.webdriver.support.wait import WebDriverWait


class TestHelpPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the help page
    """
    def setUp(self) -> None:
        """
        Sets up the HelpPage object
        """
        super().setUp()
        self.page = HelpPage(self.driver)
        self.page.launch()

    def test_at_least_one_topic_exists(self):
        """
        Test that at least one topic is on the page
        """
        WebDriverWait(self.driver,
                      10).until(lambda _: len(self.page.get_all_help_topic_elements()) != 0)

    def test_all_sidebar_contents_generated(self):
        """
        Test that the sidebar contents is exactly the list of topic headers
        """
        WebDriverWait(self.driver,
                      10).until(lambda _: self.page.get_sidenav_contents() == self.page.get_help_topic_headers())

    def test_all_topics_have_a_valid_category(self):
        """
        Test that all topics have a valid data-category="..."
        """
        WebDriverWait(self.driver,
                      10).until(lambda _: set(self.page.get_each_help_topic_category()) == set(self.page.get_valid_topics()))

    def test_all_topics_have_content(self):
        """
        Test that all topic elements have content in .panel-body
        """
        WebDriverWait(self.driver,
                      10).until(lambda _: "" not in [x.strip() for x in self.page.get_each_help_topic_content()])

    def test_filter_topics_by_category(self):
        """

        :return:
        """
        for category in self.page.get_topic_filters():
            self.page.click_category_filter(category)
            self.assertEqual(self.page.get_visible_topic_elements(),
                             [x for x in self.page.get_all_help_topic_elements() if x.get_attribute("data-category") == category or category == "all"])

    def test_filter_topics_by_fuzzy_search(self):
        """

        :return:
        """
        # Search for first word in content of first topic with filter "all"
        self.page.filter_help_topics_by_search_term(self.page.get_each_help_topic_content()[0].split()[0])
        self.assertIn(self.page.get_all_help_topic_elements()[0], self.page.get_visible_topic_elements())

        # Search for first word in header of first topic with filter "all"
        self.page.filter_help_topics_by_search_term(self.page.get_help_topic_headers()[0].split()[0])
        self.assertIn(self.page.get_all_help_topic_elements()[0], self.page.get_visible_topic_elements())

        # Search for a word not in the first topic with filter "all"
        self.page.filter_help_topics_by_search_term("veryrandomstringthatshouldnotbeintopic")
        self.assertNotIn(self.page.get_all_help_topic_elements()[0], self.page.get_visible_topic_elements())

    def test_topics_link_generation(self):
        """

        :return:
        """
        def to_link_text(text):
            return re.sub("[^A-Za-z0-9\\s]+", "", text).replace(" ", "-").lower()

        for element in self.page.get_help_topic_header_elements():
            link_element = element.find_element_by_xpath("./h3/a")
            self.assertEqual(link_element.get_attribute("href").split("#", 1)[1], to_link_text(link_element.text))
