# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import unittest
from unittest.mock import Mock, patch

from autoreduce_qp.queue_processor.reduction.process_manager import ReductionProcessManager
from autoreduce_qp.queue_processor.reduction.tests.common import (add_bad_data_and_message, add_data_and_message,
                                                                  expected_return_data_and_message)


class TestReductionProcessManager(unittest.TestCase):
    def setUp(self) -> None:
        self.data, self.message = add_data_and_message()
        self.expected_data, self.expected_message = expected_return_data_and_message()
        self.bad_data, self.bad_message = add_bad_data_and_message()
        self.run_name = "Test run name"

    def test_init(self):
        """Test that the constructor is doing what's expected"""
        self.data, self.message = add_data_and_message()

        rpm = ReductionProcessManager(self.message, self.run_name)

        assert rpm.message == self.message

    def test_run(self):
        """Tests success path"""
        run_name = "Test run name"
        rpm = ReductionProcessManager(self.message, run_name)
        result_message = rpm.run()

        self.assertEqual(result_message.facility, 'ISIS')
        self.assertEqual(result_message.instrument, 'TESTINSTRUMENT')
        self.assertEqual(result_message.run_number, '4321')
        self.assertEqual(result_message.message, None)
        self.assertEqual(
            result_message.reduction_arguments, {
                "standard_vars": {
                    "arg1": "differentvalue",
                    "arg2": 321
                },
                "advanced_vars": {
                    "adv_arg1": "advancedvalue2",
                    "adv_arg2": ""
                }
            })

    @patch('queue_processor.reduction.process_manager.docker.models.containers.Container.exec_run')
    def test_run_subprocess_error(self, docker_run: Mock):
        """Test proper handling of container encountering an error"""
        def side_effect(args, **_kwargs):
            raise Exception("test error")

        docker_run.side_effect = side_effect
        rpm = ReductionProcessManager(self.message, self.run_name)
        rpm.run()

        docker_run.assert_called_once()
        assert "Processing encountered an error" in rpm.message.message
