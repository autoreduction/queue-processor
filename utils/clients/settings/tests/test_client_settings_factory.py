# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for the ClientSettingsFactory
"""
import unittest

from utils.clients.settings.client_settings_factory import (ClientSettingsFactory, MySQLSettings, ICATSettings,
                                                            ActiveMQSettings)


# pylint:disable=missing-docstring
class TestClientSettingsFactory(unittest.TestCase):
    def setUp(self):
        self.factory = ClientSettingsFactory()

    def test_create_database(self):
        actual = self.factory.create('database',
                                     username='test-user',
                                     password='test-pass',
                                     host='test-host',
                                     port='test-port',
                                     database_name='test-name')
        self.assertIsInstance(actual, MySQLSettings)
        self.assertEqual(actual.username, 'test-user')
        self.assertEqual(actual.password, 'test-pass')
        self.assertEqual(actual.host, 'test-host')
        self.assertEqual(actual.port, 'test-port')
        self.assertEqual(actual.database, 'test-name')
        self.assertEqual(actual.get_full_connection_string(), 'mysql+mysqldb://test-user:test-pass@test-host/test-name')

    def test_create_queue(self):
        actual = self.factory.create('queue',
                                     username='test-user',
                                     password='test-pass',
                                     host='test-host',
                                     port='test-port',
                                     data_ready='test-dr')
        self.assertIsInstance(actual, ActiveMQSettings)
        self.assertEqual(actual.username, 'test-user')
        self.assertEqual(actual.password, 'test-pass')
        self.assertEqual(actual.host, 'test-host')
        self.assertEqual(actual.port, 'test-port')
        self.assertEqual(actual.data_ready, 'test-dr')

    def test_create_icat(self):
        actual = self.factory.create('icat',
                                     username='test-user',
                                     password='test-pass',
                                     host='test-host',
                                     port='test-port',
                                     authentication_type='test-auth')
        self.assertIsInstance(actual, ICATSettings)
        self.assertEqual(actual.username, 'test-user')
        self.assertEqual(actual.password, 'test-pass')
        self.assertEqual(actual.host, 'test-host')
        self.assertEqual(actual.port, 'test-port')
        self.assertEqual(actual.auth, 'test-auth')

    def test_invalid_not_a_factory(self):
        self.assertRaisesRegex(
            ValueError, f"Factories creation settings type must be one of:"
            f"{','.join(self.factory.valid_types)}", self.factory.create, 'not-factory', 'user', 'pass', 'host', 'port')

    def test_invalid_database_args(self):
        self.assertRaisesRegex(ValueError, "database_invalid is not a recognised key "
                               "word argument.",
                               self.factory.create,
                               'database',
                               'user',
                               'pass',
                               'host',
                               'port',
                               database_invalid='invalid')

    def test_invalid_queue_args(self):
        self.assertRaisesRegex(ValueError,
                               "queue_invalid is not a recognised key word argument.",
                               self.factory.create,
                               'queue',
                               'user',
                               'pass',
                               'host',
                               'port',
                               queue_invalid='invalid')

    def test_invalid_icat_args(self):
        self.assertRaisesRegex(ValueError,
                               "icat_invalid is not a recognised key word argument.",
                               self.factory.create,
                               'icat',
                               'user',
                               'pass',
                               'host',
                               'port',
                               icat_invalid='invalid')
