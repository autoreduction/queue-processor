import os
import unittest
from mock import patch

from queue_processors.queue_processor import validate_job as validate


class TestValidateJob(unittest.TestCase):

    def setUp(self):
        self.valid_nxs_location = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                               'valid.nxs')
        self.invalid_nxs_location = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 'invalid_location.nxs')
        self.zero_beam_nxs_location = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                   'zero_beam.nxs')

    def test_check_beam_current_valid(self):
        self.assertIsNone(validate.check_beam_current(self.valid_nxs_location))

    def test_check_beam_current_invalid_file_location(self):
        expected = f"Unable to read nxs file at location: {self.invalid_nxs_location}"
        actual = validate.check_beam_current(self.invalid_nxs_location)
        self.assertEqual(expected, actual)

    def test_check_beam_current_no_current(self):
        expected = f"Assuming data is invalid due to beam current value of 0.0"
        actual = validate.check_beam_current(self.zero_beam_nxs_location)
        self.assertEqual(expected, actual)

    def test_is_valid_rb_valid(self):
        self.assertIsNone(validate.is_valid_rb(100))

    def test_is_valid_rb_invalid_string(self):
        expected = "Calibration file detected (RB Number is a string)"
        actual = validate.is_valid_rb('test')
        self.assertEqual(expected, actual)

    def test_is_valid_rb_invalid_0(self):
        expected = "Calibration file detected (RB Number less than or equal to 0)"
        actual = validate.is_valid_rb(0)
        self.assertEqual(expected, actual)

    def test_validate_job_valid(self):
        self.assertIsNone(validate.validate_job(rb_number=100,
                                                file_location=self.valid_nxs_location))

    @patch('queue_processors.queue_processor.validate_job.is_valid_rb')
    @patch('queue_processors.queue_processor.validate_job.check_beam_current')
    def test_validate_job_one_invalid(self, mock_check_beam, mock_is_valid_rb):
        """
        Test that just a single expected error message if one of the validation functions fail
        As the functionality of these functions is tested above, I have mocked them here.
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
        expected = 'Invalid RB & No beam'
        mock_is_valid_rb.return_value = 'Invalid RB'
        mock_check_beam.return_value = 'No beam'
        actual = validate.validate_job(rb_number=0, file_location='')
        mock_is_valid_rb.assert_called_once()
        mock_check_beam.assert_called_once()
        self.assertEqual(expected, actual)
