# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the reduction_run_utils
"""
import unittest

from mock import Mock, patch

from queue_processors.queue_processor.queueproc_utils import reduction_run_utils as run_utils


class TestReductionRunUtils(unittest.TestCase):

    @patch('model.database.access.get_reduction_run')
    def test_get_next_version_num(self, mock_retrieve):
        """
        Test: The next version number (most recent + 1) is returned
        When: A valid ReductionRun is supplied to get_next_version_number
        """
        original_run_record = Mock()
        original_run_record.experiment.id = 111
        original_run_record.run_number = 222
        run_record_v1 = Mock()
        run_record_v2 = Mock()
        run_record_v1.run_version = 1
        run_record_v2.run_version = 2
        mock_retrieve.return_value = [run_record_v1, run_record_v2]
        version = run_utils.ReductionRunUtils.get_next_version_number(original_run_record)
        self.assertEqual(version, 3)
