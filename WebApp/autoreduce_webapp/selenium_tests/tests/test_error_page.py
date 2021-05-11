from selenium_tests.pages.error_page import ErrorPage
from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin

from autoreduce_webapp import settings
from autoreduce_webapp.view_utils import ICATConnectionException


class TestErrorPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the error page
    """
    fixtures = BaseTestCase.fixtures + ["test_overview_page"]

    def setUp(self) -> None:
        """
        Sets up the ErrorPage object
        """
        super().setUp()
        self.page = ErrorPage(self.driver)
        self.page.launch()

    def test_error_message(self):
        """
        Test that the page error message matches the expected error
        """
        settings.DEVELOPMENT_MODE = False

        expected_exception = ICATConnectionException()
        self.assertNotEqual(str(expected_exception), self.page.get_error_message())
