from selenium_tests.pages.accessibility_statement_page import AccessibilityStatementPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, \
    FooterTestMixin


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
