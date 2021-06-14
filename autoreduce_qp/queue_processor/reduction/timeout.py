# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
""" Class used for handling script timeouts"""
import signal

from autoreduce_utils.settings import SCRIPT_TIMEOUT


class TimeOut:
    """ Class used for handling script timeouts"""
    def __init__(self,
                 seconds=1,
                 error_message='Script ran for more than ' + str(SCRIPT_TIMEOUT) + ' seconds - timed out'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, *args):
        """ Handle timeout. """
        raise Exception(self.error_message)

    def __enter__(self):  # pragma: no cover
        signal.signal(signal.SIGALRM, self.handle_timeout)  # pylint: disable=no-member
        signal.alarm(self.seconds)  # pylint: disable=no-member

    def __exit__(self, _, value, traceback):  # pragma: no cover
        signal.alarm(0)  # pylint: disable=no-member
