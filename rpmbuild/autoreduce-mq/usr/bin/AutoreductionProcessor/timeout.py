import signal
from settings import MISC


class timeout:
    def __init__(self, seconds=1, error_message='Script ran for more than '
                                                + str(MISC["script_timeout"]) + ' seconds - timed out'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise Exception(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, timeout_type, value, traceback):
        signal.alarm(0)