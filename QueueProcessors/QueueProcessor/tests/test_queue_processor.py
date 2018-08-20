"""
Package to test QueueProcessor class functionality
"""

import unittest

import QueueProcessors.QueueProcessor.queue_processor as queue_processor


# pylint:disable=missing-docstring
class TestQueueProcessor(unittest.TestCase):

    def test_setup_connection(self):
        """ Basic test to ensure that setup is successful """
        try:
            queue_processor.setup_connection('Autoreduction_QueueProcessor')
        except RuntimeError as excep:
            self.fail(excep.message)

    def test_basic_main_call(self):
        """ Basic test to ensure main does not raise """
        try:
            queue_processor.main()
        except RuntimeError as excep:
            self.fail(excep.message)
