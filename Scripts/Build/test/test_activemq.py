import stomp
import unittest

class TestActiveMQ(unittest.TestCase):
        
    def test_connection_to_localhost(self):    
        c = stomp.Connection([('127.0.1.1', 61613)])
        c.start()
        c.connect('admin', 'password', wait=True)
        self.assertTrue(c.is_connected())