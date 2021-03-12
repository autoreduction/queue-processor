# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
""" Constructs a plot and DashApp object for insertion directly into a web page """

# Core Dependencies
import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash


class DashApp:
    """ Creates a DashApp for direct insertion into a web page """
    def __init__(self, figure, app_id):
        """
        Dashapp object properties
        :param figure (dictionary) plotly figure formatted as dictionary
        :param app_id (string) unique id to track dashapp persistence
        """
        self.figure = figure
        self.app_id = app_id
        self.app = self.create_dashapp()

    def create_dashapp(self):  #
        """
        Creates DjangoDash DashApp
        :return: DjangoDash DashApp (object) DashApp object for direct insertion into webapp
        """
        app = DjangoDash(self.app_id)
        app.layout = \
            html.Div([
                html.Div(
                    dcc.Graph(
                        id=self.app_id,  # Unique ID to track DashApp
                        figure=self.figure,
                    ),
                ),
            ])
        app.title = self.app_id
        return app
