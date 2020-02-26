# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the manual job submission script
"""
import unittest
import json
from mock import Mock, patch
import scripts.manual_operations.manual_submission as ms
from utils.clients.queue_client import QueueClient


# pylint:disable=too-few-public-methods
class DataFile:
    """
    Basic data file representation for testing
    """
    def __init__(self, df_name):
        self.name = df_name


def get_json_object(rb_number, instrument, data_file_location, run_number, started_by):
    """
    Return the JSON object that should be sent to DataReady
    """
    data_dict = {"rb_number": rb_number,
                 "instrument": instrument,
                 "data": data_file_location,
                 "run_number": run_number,
                 "facility": "ISIS",
                 "started_by": started_by}
    return json.dumps(data_dict)


# pylint:disable=no-self-use
class TestManualSubmission(unittest.TestCase):
    """
    Test manual_submission.py
    """
    def test_get_existing_data_file(self):
        """
        Get an existing data file name from ICAT
        """
        icat_client = Mock()
        icat_client.execute_query = Mock(return_value=[DataFile("GEM84823.nxs")])
        data_file = ms.get_data_file(icat_client, "GEM", "84823", "nxs")
        self.assertEqual(data_file.name, "GEM84823.nxs")

    def test_get_invalid_data_file(self):
        """
        Attempt to get an invalid file name from ICAT
        """
        icat_client = Mock()
        icat_client.execute_query = Mock(return_value=None)
        with self.assertRaises(SystemExit):
            ms.get_data_file(icat_client, "GEM", "84823", "jpg")

    @patch('utils.clients.queue_client.QueueClient.send', return_value=None)
    def test_submit_run(self, send):
        """
        Check that a run is submitted successfully
        """
        active_mq_client = QueueClient()
        ms.submit_run(active_mq_client, "1812345", "GEM", "5454", "nxs")
        json_obj = get_json_object("1812345", "GEM", "5454", "nxs", -1)
        send.assert_called_with('/queue/DataReady', json_obj, priority=1)
