# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import pytest

from autoreduce_qp.queue_processor.reduction.process_manager import ReductionProcessManager
from autoreduce_qp.queue_processor.reduction.tests.common import add_bad_data_and_message, add_data_and_message


class TestReductionProcessManager():
    def test_init(self):
        """Test that the constructor is doing what's expected"""
        data, message = add_data_and_message()
        run_name = "Test run name"
        rpm = ReductionProcessManager(message, run_name)

        assert rpm.message == message

    def test_run(self):
        """Tests success path"""
        data, message = add_data_and_message()
        run_name = "Test run name"
        rpm = ReductionProcessManager(message, run_name)
        result_message = rpm.run()

        assert result_message == message

    # TODO: This test should be changed to check for an exception in the Docker container
    def test_bad_run(self):
        """Tests failure path"""
        data, message = add_bad_data_and_message()
        run_name = "Test run name"
        rpm = ReductionProcessManager(message, run_name)
        result_message = rpm.run()

        assert result_message != message
