from selenium_tests.pages.help_page import HelpPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, \
    FooterTestMixin


class TestHelpPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the help page
    """
    fixtures = BaseTestCase.fixtures + ["run_help_page"]

    def setUp(self) -> None:
        """
        Sets up the HelpPage object
        """
        super().setUp()
        self.page = HelpPage(self.driver)
