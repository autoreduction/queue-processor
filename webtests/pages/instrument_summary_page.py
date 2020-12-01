from webtests.pages.component_mixins.footer_mixin import FooterMixin
from webtests.pages.component_mixins.navbar_mixin import NavbarMixin
from webtests.pages.component_mixins.tour_mixin import TourMixin
from webtests.pages.page import Page


class InstrumentSummaryPage(Page, NavbarMixin, FooterMixin, TourMixin):
    """
    Page model class for instrument summary page
    """

    @staticmethod
    def url_path():
        """
        Return the path section of the instrument url
        :return: (str) Path section of the page url
        """
        return "/instrument/%s/"