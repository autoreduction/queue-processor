# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests to exercise the code responsible for django ORM access
"""
import sys
import unittest
import os

from unittest.mock import DEFAULT, patch

from model.database import DjangoORM
from utils.project.structure import get_project_root


class TestDjangoORM(unittest.TestCase):
    def test_add_webapp_path_already_exist(self):
        """
        Test: The webapp path is not added to sys.path
        When: webapp path already exists and add_webapp_path is called
        """
        webapp_path = os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp')
        sys.path.append(webapp_path)
        expected = sys.path.count(webapp_path)
        DjangoORM.add_webapp_path()
        self.assertEqual(expected, sys.path.count(webapp_path))
        sys.path.remove(webapp_path)  # Cleanup test

    def test_add_webapp_path_not_already_exist(self):
        """
        Test: The webapp path is added to sys.path
        When: webapp path does not already exist and add_webapp_path is called
        """
        expected = os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp')
        old_sys_path = sys.path.copy()
        if expected in sys.path:
            # Remove all expected from sys.path
            sys.path = list(filter(lambda a: a != expected, sys.path))

        DjangoORM.add_webapp_path()
        self.assertIn(expected, sys.path)
        sys.path = old_sys_path  # Cleanup test

    def test_add_webapp_path_duplication(self):
        """
        Test: The path is not add more than once to sys.path
        When: add_webapp_path is called more than once
        """
        DjangoORM.add_webapp_path()
        expected = sys.path
        DjangoORM.add_webapp_path()
        self.assertEqual(expected, sys.path)

    def test_get_data_model(self):
        """
        Test: The data model can be accessed
        When: After it is imported
        """
        orm = DjangoORM()
        orm.connect()
        # pylint:disable=protected-access
        model = orm._get_data_model()
        actual = model.Instrument.objects.get_or_create(name='GEM')[0]
        self.assertIsNotNone(actual)
        self.assertEqual(actual.name, 'GEM')
        actual.delete()

    def test_get_variable_model(self):
        """
        Test: The variable model can be accessed
        When: After it is imported
        Note: This will fail if not pointing to the testing database
        """
        orm = DjangoORM()
        orm.connect()
        # pylint:disable=protected-access
        model = orm._get_variable_model()
        actual = model.Variable.objects.create(name='bool_variable', value=True, type="boolean")
        self.assertIsNotNone(actual)
        self.assertEqual(actual.name, 'bool_variable')
        self.assertEqual(actual.type, 'boolean')
        self.assertEqual(actual.value, True)
        actual.delete()

    def test_connect(self):
        """
        Test: The DjangoORM instance is exposed and populated as member variables
        When: calling the connect function
        """
        orm = DjangoORM()
        self.assertTrue(orm.connect())
        self.assertIsNotNone(orm.data_model.Instrument.objects.all())
        self.assertIsNotNone(orm.variable_model.Variable.objects.all())

    @patch('model.database.orm.DjangoORM.data_model')
    def test_failed_connect(self, mock_data):
        """
        Test: False is returned
        When: connect fails to retrieve data (raises an exception)
        """
        mock_data.Instrument.objects.first.side_effect = RuntimeError
        orm = DjangoORM()
        self.assertFalse(orm.connect())

    @staticmethod
    @patch.multiple('model.database.orm', connection=DEFAULT, close_old_connections=DEFAULT)
    def test_remove_old_db_connections_not_usable(connection, close_old_connections):
        """
        Test that old db connections are removed if they are not usable
        """
        connection.is_usable.return_value = False
        DjangoORM.remove_old_db_connections()
        connection.is_usable.assert_called_once()
        close_old_connections.assert_called_once()

    @staticmethod
    @patch.multiple('model.database.orm', connection=DEFAULT, close_old_connections=DEFAULT)
    def test_remove_old_db_connections_usable(connection, close_old_connections):
        """
        Test that old db connections are not touched if they are usable
        """
        connection.is_usable.return_value = True
        DjangoORM.remove_old_db_connections()
        connection.is_usable.assert_called_once()
        close_old_connections.assert_not_called()

    @staticmethod
    @patch.multiple('model.database.orm', connection=DEFAULT, close_old_connections=DEFAULT)
    def test_setup_django_removes_only_when_mysql(connection, close_old_connections):
        """
        Test that old db connections are not touched if they are usable
        """
        connection.is_usable.return_value = True
        with patch("WebApp.autoreduce_webapp.autoreduce_webapp.settings.DATABASES") as dbmock:
            # mocks the dict access to the DATABASE setting
            setattr(dbmock, "__getitem__", lambda self, key: {"ENGINE": "django.db.backends.mysql"})
            DjangoORM.setup_django()
            connection.is_usable.assert_called_once()
            close_old_connections.assert_not_called()

        with patch("WebApp.autoreduce_webapp.autoreduce_webapp.settings.DATABASES") as dbmock:
            # mocks the dict access to the DATABASE setting
            setattr(dbmock, "__getitem__", lambda self, key: {"ENGINE": "django.db.backends.sqlite3"})
            DjangoORM.setup_django()
            connection.is_usable.assert_called_once()
            close_old_connections.assert_not_called()
