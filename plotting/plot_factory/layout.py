# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Constructs a dashapp layout and additional layout meta parameters
"""
import logging

# Internal Dependencies
from typing import Optional

from plotting.plot_meta_language.interpreter import Interpreter


class Layout:
    """ Extract Layout as dictionary from interpreted meta data """

    # pylint: disable=too-few-public-methods
    def __init__(self, plot_style, title):
        """
        # Layout Properties

        :param plot_style (dictionary) plotly layouts formatted as dictionary
        """
        self.title = title
        self.meta_data = plot_style
        self.mode = None
        self.plot_type = None
        self.error_bars = None
        self.layout = self._extract_layout()

    def _read_plot_meta_data(self) -> Optional[dict]:
        """
        Use plot interpreter to interpret plot meta data

        :return: interpreted_layout (dictionary)
        """
        try:
            interpreted_layout = Interpreter().interpret(self.meta_data)
            return interpreted_layout
        except ImportError:
            logging.error("Could not Interpret: %s", self.meta_data)
            return None

    def _extract_layout(self):
        """
        Extracts plot layout data from plot style meta data

        :return self.meta_data (dictionary)
        """
        interpreted_layout = self._read_plot_meta_data()

        if 'mode' in interpreted_layout:
            self.mode = interpreted_layout.pop('mode')
        if 'plot' in interpreted_layout:
            self.plot_type = interpreted_layout.pop('plot')
        if 'error_bars' in interpreted_layout:
            self.error_bars = interpreted_layout.pop('error_bars')
        interpreted_layout['title'] = f"{self.title}"  # px
        return interpreted_layout
