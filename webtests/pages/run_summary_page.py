from webtests.pages.component_mixins.footer_mixin import FooterMixin
from webtests.pages.component_mixins.navbar_mixin import NavbarMixin
from webtests.pages.page import Page


class RunSummaryPage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for job queue page
    """
    @staticmethod
    def url_path():
        """
        Return the path section of the job queue url
        :return: (str) Path section of the page url
        """
        return "/runs/MARI/27877/0/"

    def get_rerun_elem(self):
        return self.get_id("re-run_and_graphs")

    def get_reduction_job_panel(self):
        return self.get_id("reduction_job_panel")