from webtests.pages.page import Page


class GraphsPage(Page):
    """
    Page model class for graphs page
    """

    @staticmethod
    def url_path():
        """
        Return the path section of the graphs url
        :return: (str) Path section of the page url
        """
        return "/graph/"