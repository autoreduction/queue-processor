import unittest
from MySQLdb import OperationalError
from stomp import exception


class TestClientConnections(unittest.TestCase):

    def test_db_conenction(self):
        try:
            from utils.clients.database import make_db_session
            _ = make_db_session()
        except OperationalError:
            raise

    def test_queue_connection(self):
        try:
            from utils.clients.queue import make_queue_session
            _ = make_queue_session()
        except exception.ConnectFailedException:
            raise
