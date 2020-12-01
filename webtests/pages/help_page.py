from webtests.pages.component_mixins.footer_mixin import FooterMixin
from webtests.pages.component_mixins.navbar_mixin import NavbarMixin
from webtests.pages.page import Page


class HelpPage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for help page
    """

    @staticmethod
    def url_path():
        """
        Return the path section of the help page
        :return: (str) Path section of the page url
        """
        return "/help/"