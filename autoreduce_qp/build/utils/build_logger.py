# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Handle the logging of build information
This is fundamentally an extra layer of functionality added to logging
"""
from __future__ import print_function

import os
import logging


class BuildLogger:
    """
    Class to handle logging for build script
    """

    logger = None

    def __init__(self, root_directory):
        # Clear log file
        self.location = os.path.join(root_directory, 'build.log')
        with open(self.location, 'w'):
            pass
        self._initialise_logger(root_directory)

    def _initialise_logger(self, root_directory):
        """
        Set up logger in given root directory and add handler
        :param root_directory: base directory of the project
        :return:
        """
        self.logger = logging.getLogger("build")
        handler = logging.FileHandler(os.path.join(root_directory, 'build.log'))
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s : %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def print_and_log(self, message, log_level=logging.INFO):
        """
        Print a message to the console and to the log file
        :param message: message to display
        :param log_level: level to log at (logging.LEVEL)
        """
        self.logger.log(level=log_level, msg=message)
        print(message)

    def print_full_log(self):
        """
        print the full log file - should only be used when errors occur
        """
        with open(self.location, 'r') as log_file:
            for line in log_file.readlines():
                print(line)
