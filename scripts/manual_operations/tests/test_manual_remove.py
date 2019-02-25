"""
Test cases for the manual job submission script
"""
import unittest
from scripts.manual_operations.manual_remove import ManualRemove


class TestManualSubmission(unittest.TestCase):
    """
    Test manual_submission.py
    """
    def setUp(self):
        self.manual_remove = ManualRemove()

    def test_find_run(self):
        """
        Check if a run exists in the database
        """
        actual = self.manual_remove.find_runs_in_database(instrument='GEM',
                                                          run_number='001')
        expected = None
        self.assertEqual(actual, expected)

    def test_find_run_invalid(self):
        """
        Check if a run does not exist in the database
        """
        actual = self.manual_remove.find_runs_in_database(instrument='TEST',
                                                          run_number='000')
        expected = None
        self.assertEqual(actual, expected)
