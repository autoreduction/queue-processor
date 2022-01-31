# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import unittest
from unittest.mock import Mock, patch
from docker.errors import APIError, ImageNotFound

from autoreduce_db.reduction_viewer.models import Software

from autoreduce_qp.queue_processor.reduction.process_manager import ReductionProcessManager
from autoreduce_qp.queue_processor.reduction.tests.common import (add_bad_data_and_message, add_data_and_message,
                                                                  expected_return_data_and_message)


class TestReductionProcessManager(unittest.TestCase):

    def setUp(self) -> None:
        self.data, self.message = add_data_and_message()
        self.expected_data, self.expected_message = expected_return_data_and_message()
        self.bad_data, self.bad_message = add_bad_data_and_message()
        self.run_name = "Test run name"
        self.software = Software(name="Mantid", version="6.2.0")

    def test_init(self):
        """Test that the constructor is doing what's expected"""
        self.data, self.message = add_data_and_message()

        rpm = ReductionProcessManager(self.message, self.run_name, self.software)

        assert rpm.message == self.message

    def test_run(self):
        """Tests success path"""
        run_name = "Test run name"
        rpm = ReductionProcessManager(self.message, run_name, self.software)
        result_message = rpm.run()

        self.assertEqual(result_message.facility, 'ISIS')
        self.assertEqual(result_message.instrument, 'TESTINSTRUMENT')
        self.assertEqual(result_message.run_number, '4321')
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

    @patch('queue_processor.reduction.process_manager.docker.models.containers.ContainerCollection.run')
    def test_run_subprocess_error(self, docker_run: Mock):
        """Test proper handling of container encountering an error"""
        docker_run.side_effect = Exception()
        rpm = ReductionProcessManager(self.message, self.run_name, self.software)
        rpm.run()
        docker_run.assert_called_once()
        assert "Processing encountered an error" in rpm.message.message

    @patch('queue_processor.reduction.process_manager.docker.models.containers.ContainerCollection.run')
    def test_missing_image(self, docker_run: Mock):
        """Test proper handling of container encountering an error"""
        docker_run.side_effect = ImageNotFound("test error")
        rpm = ReductionProcessManager(self.message, self.run_name, self.software)
        self.assertRaises(ImageNotFound, rpm.run)
        docker_run.assert_called_once()

    @patch('queue_processor.reduction.process_manager.docker.models.containers.ContainerCollection.run')
    def test_api_error(self, docker_run: Mock):
        """Test proper handling of container encountering an error"""
        docker_run.side_effect = APIError("test error")
        rpm = ReductionProcessManager(self.message, self.run_name, self.software)
        self.assertRaises(APIError, rpm.run)
        docker_run.assert_called_once()
