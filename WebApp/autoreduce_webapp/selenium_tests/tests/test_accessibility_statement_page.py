from selenium_tests.pages.accessibility_statement_page import AccessibilityStatementPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, \
    FooterTestMixin
from selenium.webdriver.support.wait import WebDriverWait


class TestAccessibilityStatementPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the accessibility statement page
    """
    def setUp(self) -> None:
        """
        Sets up the AccessibilityStatementPage object
        """
        super().setUp()
        self.page = AccessibilityStatementPage(self.driver)
        self.page.launch()

    def test_accessibility_statement_contents_appears(self):
        """
        Test that the <div> #accessibility-statement-contents is visible and contains text
        """
        WebDriverWait(self.driver,
                      10).until(lambda _: self.page.get_accessibility_statement_contents_element().is_displayed())

        WebDriverWait(
            self.driver,
            10).until(lambda _: self.page.get_accessibility_statement_contents_element().text.replace(" ", "") != "")
