# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import unittest
import pytest

from autoreduce_qp.queue_processor.reduction.process_manager import ReductionProcessManager
from autoreduce_qp.queue_processor.reduction.tests.common import add_data_and_message


class TestReductionProcessManager(unittest.TestCase):
    def setUp(self) -> None:
        self.data, self.message = add_data_and_message()
        self.run_name = "Test run name"

    def test_init(self):
        """Test that the constructor is doing what's expected"""
        rpm = ReductionProcessManager(self.message, self.run_name)

        assert rpm.message == self.message

    # TODO: Write test for failure path - it should raise an exception in the Docker container

    def test_run(self):
        """Tests success path - it uses side effect to set the expected output file rather than raise an exception"""
        rpm = ReductionProcessManager(self.message, self.run_name)
        result_message = rpm.run()

        assert result_message == self.message
