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

    def test_at_least_one_topic_exists(self):
        """
        Test that at least one topic is on the page
        """
        self.assertTrue(len(self.page.get_help_topic_elements()) != 0)

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
                      10).until(lambda _: set(self.page.get_each_help_topic_category()) == set(self.page.get_topic_filters()).remove("all"))

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
                             [x for x in self.page.get_help_topic_elements() if x.get_attribute("data-category") == category or category == "all"])

        # Reset category to All (default)
        self.page.click_category_filter("all")

    # def test_filter_topics_by_fuzzy_search(self):
    #     """
    #
    #     :return:
    #     """

    def test_topics_link_generation(self):
        """

        :return:
        """
        def to_link_text(text):
            return text.strip().replace(" ", "-").replace(r"/[^a-z0-9\s]/gi", "").replace(r"/[_\s]/g", '-').lower()

        for element in self.page.get_help_topic_header_elements():
            link_element = element.find_element_by_xpath("./h3/a")
            self.assertEqual(link_element.get_attribute("href"), to_link_text(link_element.text))
