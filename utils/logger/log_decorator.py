# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Log Decorator
"""
import functools
from utils.logger.log_handler import GetLogger as get_Logger


class LogDecorator(object):
    """Log Class Decorator"""

    def __init__(self, logger, log_level=None, log_file_name=None, stream_log=None):
        # self.log_level = log_level
        # self.log_file_name = log_file_name
        # self.stream_log = stream_log
        self.logger = logger

    def __call__(self, fn):
        @functools.wraps(fn)
        def decorated_logger(*args, **kwargs):
            """
            Execute logging utility as decorator around a given method
            :param args:
            :param kwargs:
            :return: (function/exception)
            """
            logger = self.logger.logger

            try:
                logger.debug(f"Method: {fn.__name__} Arguments: {args} {kwargs}")
                print("logging inside decorator")
                return fn(*args, **kwargs)
            except Exception as ex:
                logger.debug("Exception {0}".format(ex))
                raise ex
        return decorated_logger


