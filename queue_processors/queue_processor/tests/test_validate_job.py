# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for functions that valid an autoreduction job should run
"""
import unittest
from mock import patch

from queue_processors.queue_processor import validate_job as validate
from testing_data import VALID_NEXUS, ZERO_BEAM_NEXUS


class TestValidateJob(unittest.TestCase):
    """
    Test cases for functions that validate if an autoreduction job should run
    """

    def setUp(self):
        """ create locations for valid, invalid and zero beam nxs files """
        self.valid_nxs_location = VALID_NEXUS
        self.invalid_nxs_location = 'invalid_location.nxs'
        self.zero_beam_nxs_location = ZERO_BEAM_NEXUS

    def test_check_beam_current_valid(self):
        """ Validation should return None if all is okay """
        self.assertIsNone(validate.check_beam_current(self.valid_nxs_location))

    def test_check_beam_current_invalid_file_location(self):
        """ Ensure that the correct error message is returned if file does not exist """
        expected = f"Unable to read nxs file at location: {self.invalid_nxs_location}"
        actual = validate.check_beam_current(self.invalid_nxs_location)
        self.assertEqual(expected, actual)

    def test_check_beam_current_no_current(self):
        """ Ensure that the correct error message is returned if the nexus file has no beam """
        expected = f"Assuming data is invalid due to beam current value of 0.0"
        actual = validate.check_beam_current(self.zero_beam_nxs_location)
        self.assertEqual(expected, actual)

    def test_is_valid_rb_valid(self):
        """ Assert none is returned for valid RB """
        self.assertIsNone(validate.is_valid_rb(100))

    def test_is_valid_rb_invalid_string(self):
        """ Ensure that the correct error message is returned if the RB is a string """
        expected = "Calibration file detected (RB Number is not an integer)"
        actual = validate.is_valid_rb('test')
        self.assertEqual(expected, actual)

    def test_is_valid_rb_invalid_0(self):
        """ Ensure that the correct error message is returned if the RB is 0 or less"""
        expected = "Calibration file detected (RB Number less than or equal to 0)"
        actual = validate.is_valid_rb(0)
        self.assertEqual(expected, actual)

    def test_validate_job_valid(self):
        """ Assert none is returned if all validation checks pass"""
        self.assertIsNone(validate.validate_job(rb_number=100,
                                                file_location=self.valid_nxs_location))

    @patch('queue_processors.queue_processor.validate_job.is_valid_rb')
    @patch('queue_processors.queue_processor.validate_job.check_beam_current')
    def test_validate_job_one_invalid(self, mock_check_beam, mock_is_valid_rb):
        """
        Test that just a single expected error message is returned if one of the validation
        functions fail.
        As the functionality of the actual validation functions is tested above,
        I have mocked them here so we only test the logic of the error construction.
        """
        expected = 'Invalid RB'
        mock_is_valid_rb.return_value = expected
        mock_check_beam.return_value = None
        actual = validate.validate_job(rb_number=0, file_location='')
        mock_is_valid_rb.assert_called_once()
        mock_check_beam.assert_called_once()
        self.assertEqual(expected, actual)

    @patch('queue_processors.queue_processor.validate_job.is_valid_rb')
    @patch('queue_processors.queue_processor.validate_job.check_beam_current')
    def test_validate_job_two_invalid(self, mock_check_beam, mock_is_valid_rb):
        """ Test that both error messages are returned if both validation checks fail"""
        expected = 'Invalid RB & No beam'
        mock_is_valid_rb.return_value = 'Invalid RB'
        mock_check_beam.return_value = 'No beam'
        actual = validate.validate_job(rb_number=0, file_location='')
        mock_is_valid_rb.assert_called_once()
        mock_check_beam.assert_called_once()
        self.assertEqual(expected, actual)

    def test_float_mean_valid(self):
        """ Ensure that the mean for a list of floats is correctly calculated """
        expected = 2.0
        actual = validate.float_mean([1.0, 2.0, 3.0])
        self.assertEqual(expected, actual)
