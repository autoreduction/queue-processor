import unittest
from utils.clients.abstract_client import AbstractClient
from utils.clients.client_settings import ClientSettings


class TestAbstractClient(unittest.TestCase):

    def test_client_settings_init(self):
        valid_settings = ClientSettings(username='user',
                                        password='pass',
                                        host='host',
                                        port='123')
        try:
            interface = ClientWrapper(credentials=valid_settings)
        except TypeError:
            self.fail("Expected creation with valid settings not to fail but it did.")
        self.assertIsNotNone(interface)

    def test_derived_client_settings_init(self):
        class DerivedSettings(ClientSettings):
            pass
        derived_settings = DerivedSettings(username='user',
                                           password='pass',
                                           host='host',
                                           port='123')
        try:
            interface = ClientWrapper(credentials=derived_settings)
        except TypeError:
            self.fail("Expected creation with valid settings not to fail but it did.")
        self.assertIsNotNone(interface)

    def test_invalid_init(self):
        self.assertRaisesRegexp(TypeError, "Expected instance of ClientSettings not <type 'int'>",
                                ClientWrapper, 10)
        self.assertRaisesRegexp(TypeError, "Expected instance of ClientSettings not <type 'str'>",
                                ClientWrapper, 'string')
        self.assertRaisesRegexp(TypeError, "Expected instance of ClientSettings not <type 'list'>",
                                ClientWrapper, [1, 2, 3, 4])


class ClientWrapper(AbstractClient):
    """
    A wrapper class to allow access to abstract methods
    """
    def connect(self):
        pass

    def disconnect(self):
        pass

    def _test_connection(self):
        pass
