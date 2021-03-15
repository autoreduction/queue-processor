from time import sleep

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
                             [x for x in self.page.get_all_help_topic_elements() if x.get_attribute("data-category") == category or category == "all"])

        # Reset category to All (default)
        self.page.click_category_filter("all")

    def test_filter_topics_by_fuzzy_search(self):
        """

        :return:
        """
        valid_searches = ["Lorem", "Siit", "vOlUptateM", "Header Two"]
        invalid_searches = ["randomtext", "very Random text 123456789", "£$%^&"]

        mock_categories = self.page.get_topic_filters()
        mock_categories.remove("all")

        for mock_category in mock_categories:
            for filter_by_category in self.page.get_topic_filters():
                # Create mock topic element
                self.driver.execute_script(f"""
document.getElementById("help-topics").innerHTML = `
    <section id="mock-help-topic" class="help-topic panel panel-default" data-category="{mock_category}">
        <div class="panel-heading">
            <h3>Lorem Ipsum</h3>
        </div>
        <div class="panel-body">
            <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum
            </p>
            <h4>Header One</h4>
            <ol>
                <li>Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.</li>
                <li>Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.</li>
            </ol>
            <h4>Header Two</h4>
            <p>Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem.</p>
        </div>
    </section>
` + document.getElementById("help-topics").innerHTML; 
                    """)
                self.page.click_category_filter(filter_by_category)

                sleep(10)

                mock_help_topic = self.page.get_mock_help_topic()

                if filter_by_category != "all" and mock_category != filter_by_category:
                    self.assertNotIn(mock_help_topic, self.page.get_visible_topic_elements())
                    continue

                for search in valid_searches:
                    self.page.filter_help_topics_by_search_term(search)
                    self.assertIn(mock_help_topic, self.page.get_visible_topic_elements())

                for search in invalid_searches:
                    self.page.filter_help_topics_by_search_term(search)
                    self.assertNotIn(mock_help_topic, self.page.get_visible_topic_elements())

        # Reset filters
        self.page.click_category_filter("all")
        self.page.filter_help_topics_by_search_term("")

    def test_topics_link_generation(self):
        """

        :return:
        """
        def to_link_text(text):
            return text.strip().replace(" ", "-").replace(r"/[^a-z0-9\s]/gi", "").replace(r"/[_\s]/g", '-').lower()

        for element in self.page.get_help_topic_header_elements():
            link_element = element.find_element_by_xpath("./h3/a")
            self.assertEqual(link_element.get_attribute("href"), to_link_text(link_element.text))
