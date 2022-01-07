# ############################################################################### #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
from pathlib import Path
from shutil import rmtree
from unittest import TestCase

from autoreduce_utils.settings import CYCLE_DIRECTORY, ARCHIVE_ROOT, SCRIPTS_DIRECTORY

from autoreduce_qp.systemtests.utils.data_archive import DataArchive


class TestDataArchive(TestCase):

    def setUp(self) -> None:
        if Path(ARCHIVE_ROOT).exists():
            rmtree(ARCHIVE_ROOT)
        self.instrument = "TEST"
        self.data_archive = DataArchive([self.instrument], 19, 20)
        self.expected_cycle_path = Path(CYCLE_DIRECTORY % (self.instrument, "19_1")).parent
        self.expected_script_path = Path(SCRIPTS_DIRECTORY % self.instrument)

    def tearDown(self) -> None:
        if Path(ARCHIVE_ROOT).exists():
            rmtree(ARCHIVE_ROOT)

    def test_delete(self):
        """
        Tests the delete method removes the data-archive
        """
        test_archive_path = Path(CYCLE_DIRECTORY)
        test_archive_path.mkdir(parents=True)
        self.assertTrue(test_archive_path.exists())
        self.data_archive.delete()
        self.assertFalse(test_archive_path.exists())

    def test_delete_post_create(self):
        """
        Tests delete when archvie was created from create
        """
        self.data_archive.create()
        self.data_archive.delete()
        self.assertFalse(self.expected_cycle_path.exists())

    def test_create(self):
        """
        Tests the data-archive is created with the correct structure in the correct place
        """
        self.data_archive.create()
        self.assertTrue(self.expected_cycle_path.exists())
        self.assertTrue(self.expected_script_path.exists())

    def test_add_data_file(self):
        """
        Tests that a datafile can be added in the correct location with the correct name
        """
        expected_data_file = self.expected_cycle_path / "cycle_19_1" / "datafile.nxs"
        result = self.data_archive.add_data_file(self.instrument, "datafile.nxs", 19, 1)
        self.assertEqual(str(expected_data_file), result)
        self.assertTrue(expected_data_file.exists())

    def test_add_reduction_script(self):
        """
        Tests that a reduction script can be added with the correct text
        """
        expected_script_file = self.expected_script_path / "reduce.py"
        expected_script_text = "print('hello')\nprint('world')"
        self.data_archive.create()
        self.data_archive.add_reduction_script(self.instrument, expected_script_text)
        self.assertTrue(expected_script_file.exists())
        with open(expected_script_file, encoding="utf-8") as fle:
            actual_text = fle.read()
        self.assertEqual(expected_script_text, actual_text)

    def test_add_reduce_vars_script(self):
        """
        Tests that a reduce vars script can be added with the correct text
        """
        expected_var_file = self.expected_script_path / "reduce_vars.py"
        expected_var_text = "vars = {}"
        self.data_archive.create()
        self.data_archive.add_reduce_vars_script(self.instrument, expected_var_text)
        self.assertTrue(expected_var_file.exists())
        with open(expected_var_file, encoding="utf-8") as fle:
            actual_text = fle.read()
        self.assertEqual(expected_var_text, actual_text)
