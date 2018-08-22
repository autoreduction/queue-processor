""" Class used for handling script timeouts"""
import signal
# pylint:disable=no-name-in-module,import-error
from queue_processors.reduction_processor.settings import MISC


class TimeOut(object):
    """ Class used for handling script timeouts"""
    # pylint: disable=too-few-public-methods
    def __init__(self,
                 seconds=1,
                 error_message='Script ran for more than ' + str(MISC["script_timeout"]) +
                 ' seconds - timed out'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self):
        """ Handle timeout. """
        raise Exception(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)  # pylint: disable=no-member
        signal.alarm(self.seconds)  # pylint: disable=no-member

    def __exit__(self, timeout_type, value, traceback):
        signal.alarm(0)  # pylint: disable=no-member
