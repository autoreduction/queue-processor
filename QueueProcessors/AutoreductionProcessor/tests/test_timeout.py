import unittest
import signal
from signal import alarm

from mock import call, patch

from QueueProcessors.AutoreductionProcessor.timeout import timeout


class TestTimeOut(unittest.TestCase):

    def setUp(self):
        self.timeout = timeout(seconds=10,
                               error_message='test error message')
        alarm(10)

    def test_init(self):
        self.assertEqual(self.timeout.seconds, 10)
        self.assertEqual(self.timeout.error_message, 'test error message')

    def test_handle_timeout(self):
        self.assertRaises(Exception, self.timeout.handle_timeout)

    @patch('signal.signal')
    @patch('signal.alarm')
    def test_enter(self, mock_alarm, mock_signal):
        self.timeout.__enter__()
        mock_signal.assert_called_once_with(call(signal.SIGALRM,
                                                 self.timeout.handle_timeout))
        mock_alarm.assert_called_once_with(call(10))

    @patch('signal.alarm')
    def test_exit(self, mock_alarm):
        self.timeout.__exit__('test', 'test', 'test')
        mock_alarm.assert_called_once_with(call('test', 'test', 'test'))
