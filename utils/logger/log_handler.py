# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
A module for gathering and persistently storing data collected about Autoreductions state and
performance.
"""

# Internal Dependencies

# External Dependencies
import sys
import os
import logging
import inspect


class GetLogger:
    """Class to initialise logging when called"""
    def __init__(self, log_level=None, log_file_name=None, stream_log=None):
        """
        :param log_level: (str) level to log
        :param log_file_name: (str) filename to log too - Default is script name calling GetLogger
        :param stream_log: (Bool) True or False to stream_log log to console when running
        """
        # self.log_level = log_level
        # self.message = message

        # # Set log file name equal to callers filename with .log extension appended if None
        caller_frame = os.path.abspath((inspect.stack()[1])[1])
        caller_file_name = f"{os.path.splitext(os.path.basename(caller_frame))[0]}.log"
        self.log_file_name = log_file_name if log_file_name is not None else caller_file_name

        self.stream_log = stream_log if stream_log is not None else False  # Toggle Stream logs
        self.log_level = log_level.upper() if log_level is not None else 'DEBUG'  # default is debug
        self.logger = self.create_logger()

    @staticmethod
    def set_log_level(log_level):
        """Sets log level
        :param log_level:
        :return: (int) Log Level Attribute
        """
        return getattr(sys.modules[logging.__name__], log_level)

    @staticmethod
    def set_log_format():
        """Set log format
        :return: (class attr) logging.formatter
        """
        return logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

    def set_stream_handler(self):
        """Adds stream_log handler to output to terminal
        :return stream_handler: sss(class attr) logging.StreamHandler
        """

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(self.set_log_format())
        return stream_handler

    def create_logger(self):
        """Create logger
        :return logger: (class attr) logging.Logger
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(self.set_log_level(self.log_level))

        file_handler = logging.FileHandler(self.log_file_name)
        file_handler.setLevel(self.set_log_level(self.log_level))  # remove if useless
        file_handler.setFormatter(self.set_log_format())
        # file_handler.setFormatter()
        logger.addHandler(file_handler)

        if self.stream_log:
            logger.addHandler(self.set_stream_handler())

        print("logging from log handler")
        return logger
