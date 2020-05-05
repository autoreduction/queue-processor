import sys
import unittest
import os

from mock import patch

from model.database.orm import DjangoORM
from utils.project.structure import get_project_root


class TestDjangoORM(unittest.TestCase):

    def test_add_webapp_path(self):
        """
        Test: The correct path is added to sys.path
        When: add_webapp_path is called
        """
        path = sys.path
        expected = os.path.join(get_project_root(), 'WebApp', 'autoreduce_webapp')
        DjangoORM.add_webapp_path()
        self.assertTrue(expected in path)
        sys.path.remove(expected)  # Cleanup test

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
        Test: That the data model can be accessed
        When: After it is imported
        """
        orm = DjangoORM()
        orm.connect()
        model = orm._get_data_model()
        actual = model.Instrument.objects.filter(name='GEM').first()
        self.assertIsNotNone(actual)
        self.assertEqual(actual.name, 'GEM')

    def test_get_variable_model(self):
        """
        Test: That the variable model can be accessed
        When: After it is imported
        """
        orm = DjangoORM()
        orm.connect()
        model = orm._get_variable_model()
        actual = model.Variable.objects.filter(name='bool_variable').first()
        self.assertIsNotNone(actual)
        self.assertEqual(actual.name, 'bool_variable')
        self.assertEqual(actual.type, 'boolean')

    def test_connect(self):
        """
        Test: The orm is exposed and populated as member variables
        When: calling the connect function
        """
        orm = DjangoORM()
        self.assertTrue(orm.connect())
        self.assertIsNotNone(orm.data_model.Instrument.objects.first())
        self.assertIsNotNone(orm.variable_model.Variable.objects.first())

    @patch('model.database.orm.DjangoORM.data_model')
    def test_failed_connect(self, mock_data):
        """
        Test: False is returned
        When: Connect fails to retrieve data (raises an exception)
        """
        mock_data.Instrument.objects.first.side_effect = RuntimeError
        orm = DjangoORM()
        self.assertFalse(orm.connect())
