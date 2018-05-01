"""
A full end to end system test of the code
"""
import json
import unittest

# from autoreduce.utils.client import queue_client, database_client
# from autoreduce.utils.testhelpers import data_archive_creator


class TestEndToEnd(unittest.TestCase):

    def setUp(self):
        # flush database
        #self.queue_connection = queue_client.get_connection()
        #self.archive_creator = data_archive_creator.make_full_archive()
        pass

    def test_gem_end_to_end(self):
        send_data_to_queue("1", "GEM", "path/to/file", "000001", self.queue_connection)
        # monitor execution somehow?
        # check that the file has been successfully reduced in the db
        pass

    def test_wish_end_to_end(self):
        send_data_to_queue("2", "WISH", "path/to/file", "000002", self.queue_connection)
        # monitor execution somehow?
        # check that the file has been successfully reduced in the db
        pass

    def test_polaris_end_to_end(self):
        send_data_to_queue("3", "POLARIS", "path/to/file", "000003", self.queue_connection)
        # monitor execution somehow?
        # check that the file has been successfully reduced in the db
        pass

    def test_polref_end_to_end(self):
        send_data_to_queue("4", "POLREF", "path/to/file", "000004", self.queue_connection)
        # monitor execution somehow?
        # check that the file has been successfully reduced in the db
        pass

    def test_osiris_end_to_end(self):
        send_data_to_queue("5", "OSIRIS", "path/to/file", "000005", self.queue_connection)
        # monitor execution somehow?
        # check that the file has been successfully reduced in the db
        pass


def send_data_to_queue(rb_number, instrument, location, run_number, queue_processor_connection):
    data_to_send = {'rb_number': rb_number,
                    'instrument': instrument,
                    'data': location,
                    'run_number': run_number,
                    'facility': 'ISIS'}
    queue_processor_connection.send('/queue/DataReady',
                                    json.dumps(data_to_send),
                                    priority='9')
