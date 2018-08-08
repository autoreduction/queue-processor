import unittest

from utils.clients.settings.client_settings import ClientSettings


class TestClientSettings(unittest.TestCase):

    def test_valid_init(self):
        try:
            settings = ClientSettings(username='user',
                                      password='pass',
                                      host='host',
                                      port='123')
        except ValueError:
            self.fail("Expected creation with valid parameters not to fail but it did.")
        self.assertIsNotNone(settings)
        self.assertEqual(settings.username, 'user')
        self.assertEqual(settings.password, 'pass')
        self.assertEqual(settings.host, 'host')
        self.assertEqual(settings.port, '123')

    def test_invalid_init(self):
        self.assertRaisesRegexp(ValueError, "123 of <type 'int'> is not a string",
                                ClientSettings, 'string', 123, True, 99.99)
        self.assertRaisesRegexp(ValueError, "True of <type 'bool'> is not a string",
                                ClientSettings, 'string', 'string', True, 99.99)
        self.assertRaisesRegexp(ValueError, "99.99 of <type 'float'> is not a string",
                                ClientSettings, 'string', 'string', 'string', 99.99)


