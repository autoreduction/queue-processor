"""
Test cases for the manual job submission script
"""
import unittest
import json
from mock import Mock
import scripts.manual_submission_script.manual_submission as ms

# pylint:disable=too-few-public-methods
class DataFile(object):
    """
    Basic data file representation for testing
    """
    def __init__(self, df_name):
        self.name = df_name

def get_json_object(rb_number, instrument, data_file_location, run_number):
    """
    Return the JSON object that should be sent to DataReady
    """
    data_dict = {"rb_number": rb_number,
                 "instrument": instrument,
                 "data": data_file_location,
                 "run_number": run_number,
                 "facility": "ISIS"}
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

    def test_submit_run(self):
        """
        Check that a run is submitted successfully
        """
        active_mq_client = Mock()
        active_mq_client.send = Mock(return_value=None)
        ms.submit_run(active_mq_client, "1812345", "GEM", "5454", "nxs")
        json_obj = get_json_object("1812345", "GEM", "5454", "nxs")
        active_mq_client.send.assert_called_with('/queue/DataReady', json_obj, priority=1)
