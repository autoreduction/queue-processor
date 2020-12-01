from webtests.pages.component_mixins.footer_mixin import FooterMixin
from webtests.pages.component_mixins.navbar_mixin import NavbarMixin
from webtests.pages.page import Page


class JobQueuePage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for job queue page
    """

    @staticmethod
    def url_path():
        """
        Return the path section of the job queue url
        :return: (str) Path section of the page url
        """
        return "/runs/queue/"