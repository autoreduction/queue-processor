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

    def test_all_sidebar_contents_generated(self):
        """
        Test that the number of elements in the sidebar equals the number of
        topics on the page
        """
        WebDriverWait(self.driver,
                      30).until(lambda _: len(self.page.get_sidenav_contents()) == len(self.page.get_help_topics()))
