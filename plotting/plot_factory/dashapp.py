# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Constructs a plot and DashApp object for insertion into directly into a web page
"""

# Core Dependencies
import dash
import dash_core_components as dcc
import dash_html_components as html


class DashApp:  # pylint: disable=too-few-public-methods
    """Creates a DashApp for direct insertion into a web page"""
    def __init__(self, figure, app_id):
        """
        Dashapp object properties
        :param figure (dictionary)
        :param app_id (string)
        """
        self.figure = figure
        self.app_id = app_id
        self.app = self.create_dashapp()

    def create_dashapp(self):  # pylint: disable=too-few-public-methods
        """
        Creates DashApp
        :return: DashApp (object) DashApp object for direct insertion into webapp
        """
        app = dash.Dash()
        app.layout = html.Div([
            html.Div(
                dcc.Graph(
                    id=self.app_id,  # Unique ID to track DashApp
                    figure=self.figure
                )
            )
        ])
        return app
