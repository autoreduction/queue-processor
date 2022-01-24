# ############################################################################ #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
"""Tests for parts of the reduction_service."""
import io
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, Mock, PropertyMock, call, patch
from parameterized import parameterized

from autoreduce_utils.settings import CEPH_DIRECTORY, SCRIPTS_DIRECTORY
from autoreduce_qp.queue_processor.reduction.exceptions import DatafileError, ReductionScriptError
from autoreduce_qp.queue_processor.reduction.service import (Datafile, ReductionDirectory, ReductionScript,
                                                             TemporaryReductionDirectory, reduce)
from autoreduce_qp.queue_processor.reduction.tests.module_to_import import TEST_DICTIONARY

REDUCTION_SERVICE_DIR = "autoreduce_qp.queue_processor.reduction.service"


# pylint:disable=protected-access
class TestReductionService(unittest.TestCase):
    """
    Test cases for classes and functions of reduction_service
    """

    def setUp(self) -> None:
        patch(f"{REDUCTION_SERVICE_DIR}.LOGGER")
        self.instrument = "testinstrument"
        self.run_number = "123"
        self.rb_number = "1234"
        self.datafile = MagicMock()
        self.script = MagicMock()
        self.temp_dir = MagicMock()
        self.reduction_dir = MagicMock()
        self.reduction_arguments = {
            "standard_vars": {
                "arg1": "somevalue",
                "arg2": 123
            },
            "advanced_vars": {
                "adv_arg1": "advancedvalue",
                "adv_arg2": ""
            }
        }
        self.log_stream = MagicMock()

    @contextmanager
    def _test_module(self, test_string: str):
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix=".py") as script_file:
            script_file.write(test_string)
            script_file.flush()
            script_path = Path(script_file.name)
            red_script = ReductionScript(self.instrument, script_path=script_path)
            red_script.load()
            yield red_script

    def test_reduction_directory_init_(self):
        """
        Test: correct fields setup
        When: Object is created
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number, 0)
        expected_path = Path(CEPH_DIRECTORY % (self.instrument, self.rb_number, self.run_number)) / "run-version-0"
        expected_log_path = expected_path / "reduction_log"
        expected_mantid_log = expected_log_path / f"RB_{self.rb_number}_" \
                                                  f"Run_{self.run_number}_Mantid.log"
        expected_script_log = expected_log_path / f"RB_{self.rb_number}_" \
                                                  f"Run_{self.run_number}_Script.out"
        self.assertEqual(expected_path, reduction_dir.path)
        self.assertEqual(expected_log_path, reduction_dir.log_path)
        self.assertEqual(expected_mantid_log, reduction_dir.mantid_log)
        self.assertEqual(expected_script_log, reduction_dir.script_log)

    @parameterized.expand([[1], [2], [20]])
    def test_reduction_directory_version_applied(self, run_number: int):
        """
        Test: correct fields setup
        When: Object is created
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number, run_number)
        expected_path = Path(CEPH_DIRECTORY %
                             (self.instrument, self.rb_number, self.run_number)) / f"run-version-{run_number}"
        self.assertEqual(expected_path, reduction_dir.path)

    def test_reduction_directory_create(self):
        """
        Test: Directory is created
        When: create is called
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number, 0)
        with TemporaryDirectory() as directory:
            reduction_dir.path = Path(directory) / "head"
            reduction_dir.log_path = reduction_dir.path / "reduction_log"
            reduction_dir.script_log = reduction_dir.log_path / "script.out"
            reduction_dir.mantid_log = reduction_dir.log_path / "mantid.log"
            reduction_dir.create()
            self.assertTrue(reduction_dir.path.exists())
            self.assertTrue(reduction_dir.log_path.exists())
            self.assertTrue(reduction_dir.mantid_log.exists())
            self.assertTrue(reduction_dir.script_log.exists())

    # TempReductionDirectory Tests
    def test_temp_reduction_directory_init(self):
        """
        Tests: Temporary directory is created and populated
        When: object is created
        """
        temp_dir = TemporaryReductionDirectory(self.rb_number, self.run_number)
        self.assertTrue(temp_dir.exists())
        self.assertTrue(temp_dir.log_path.exists())
        self.assertTrue(temp_dir.mantid_log.exists())
        self.assertTrue(temp_dir.script_log.exists())
        self.assertEqual("reduction_log", temp_dir.log_path.name)
        self.assertEqual(f"RB_{self.rb_number}_Run_{self.run_number}_Mantid.log", temp_dir.mantid_log.name)
        self.assertEqual(f"RB_{self.rb_number}_Run_{self.run_number}_Script.out", temp_dir.script_log.name)
        temp_dir.delete()
        self.assertFalse(temp_dir.exists())

    def test_temp_reduction_directory_delete(self):
        """
        Tests: Temporary Directory is deleted
        When: Delete is called
        """
        temp_dir = TemporaryReductionDirectory(self.rb_number, self.rb_number)
        self.assertTrue(temp_dir.exists())
        temp_dir.delete()
        self.assertFalse(temp_dir.exists())

    def test_temporary_reduction_directory_copy(self):
        """
        Tests: Directory is copied
        When: copy is called
        """
        with TemporaryDirectory() as dest, TemporaryDirectory() as src:
            temp_reduction_dir = TemporaryReductionDirectory(self.instrument, self.rb_number)
            dest_folder = Path(dest)
            src_folder = Path(src)
            temp_reduction_dir._path = src_folder
            fill_mockup_directory(temp_reduction_dir._path)

            temp_reduction_dir.copy(dest_folder)
            self.assertTrue((dest_folder / "myfile.nxs").exists())
            self.assertTrue((dest_folder / "reduction_log").exists())
            self.assertTrue((dest_folder / "reduction_log" / "script.out"))

    # Datafile Tests
    @patch(f"{REDUCTION_SERVICE_DIR}.os.access", return_value=True)
    def test_datafile_init_file_readable(self, _):
        """
        Tests: datafile path is setup
        When: datafile is created
        """
        datafile = Datafile("/path/to/file.png")
        self.assertEqual(Path("/path/to/file.png"), datafile.path)

    @patch(f"{REDUCTION_SERVICE_DIR}.os.access", return_value=False)
    def test_datafile_init_non_readable_throws_datafile_error(self, _):
        """
        Tests: DatafileError is raised
        When: There is a problem reading the datafile
        """
        with self.assertRaises(DatafileError):
            Datafile("/path/to/file.nxs")

    # Reduction Script Tests
    def test_reduction_script_init(self):
        """
        Tests: Correct fields set up
        When: reduction script object is created
        """
        script = ReductionScript(self.instrument)
        self.assertEqual(Path(SCRIPTS_DIRECTORY % self.instrument) / "reduce.py", script.script_path)
        self.assertEqual([], script.skipped_runs)
        self.assertIsNone(script.module)

        script = ReductionScript(self.instrument, script_path="test_script.py")
        self.assertEqual(Path("test_script.py"), script.script_path)

    def test_reduction_script_run(self):
        """
        Tests: Correct fields set up
        When: reduction script object is created
        """
        script = ReductionScript(self.instrument)

        script.module = Mock()
        script.run([Datafile("/tmp")], Datafile("/tmp"))

        script.module.main.assert_called_once()

    def test_reduction_script_load(self):
        """
        Test importing a module that is all OK
        """
        script_path = Path(os.path.join(os.path.dirname(__file__), "module_to_import.py"))
        red_script = ReductionScript(self.instrument, script_path=script_path)
        module = red_script.load()

        assert red_script.exists()
        assert getattr(module, "TEST_DICTIONARY") == TEST_DICTIONARY
        assert red_script.module is not None

    def test_reduction_script_load_invalid_module(self):
        """
        Test importing a module that does not exist
        """
        script_path = Path("some.module.that.does.not.exist")
        red_script = ReductionScript(self.instrument, script_path=script_path)
        with self.assertRaises(ImportError):
            red_script.load()

    def test_reduction_script_load_syntax_error(self):
        """
        Test importing a module that has a syntax error in it
        """
        module_with_syntax_error_str = """TEST_DICTIONARY = {"key1": "value1"""
        with self.assertRaises(SyntaxError):
            with self._test_module(module_with_syntax_error_str):
                pass

    @patch("io.open", side_effect=IOError)
    def test_reduction_script_text_ioerror(self, _: Mock):
        """
        Test throwing an IOError just gives empty text
        """
        red_script = ReductionScript(self.instrument)
        assert red_script.text() == ""

    def test_reduction_script_text(self):
        """
        Test that the script text is correctly loaded
        """
        test_string = 'print(123)'
        with self._test_module(test_string) as red_script:
            assert red_script.text() == test_string

        test_special_chars = 'print("✈", "’")'
        with self._test_module(test_special_chars) as red_script:
            assert red_script.text() == test_special_chars

    def test_reduction_script_replace_variables_before_load(self):
        """
        Test that replace variables raises if called before the module is loaded
        """
        script_path = Path("/tmp/file")
        red_script = ReductionScript(self.instrument, script_path=script_path)
        self.assertRaises(RuntimeError, red_script.replace_variables, self.reduction_arguments)

    def test_reduction_script_replace_variables(self):
        """
        Test that replace variables properly replaces the web_var dictionary in the module
        """
        test_string = 'print(123)'
        with self._test_module(test_string) as red_script:
            red_script.replace_variables(self.reduction_arguments)
            assert red_script.text() == test_string

        assert red_script.module.web_var.standard_vars["arg1"] == "somevalue"
        assert red_script.module.web_var.standard_vars["arg2"] == 123
        assert red_script.module.web_var.advanced_vars["adv_arg1"] == "advancedvalue"
        assert red_script.module.web_var.advanced_vars["adv_arg2"] == ""

    def test_reduction_script_replace_variables_when_web_var_not_dict(self):
        """
        Test that replace variables properly replaces the web_var dictionary in the module
        when the web_var attribute is NOT a dictionary
        """
        test_string = 'web_var=123\nprint(123)'
        with self._test_module(test_string) as red_script:
            red_script.replace_variables(self.reduction_arguments)
            assert red_script.text() == test_string

        assert red_script.module.web_var.standard_vars["arg1"] == "somevalue"
        assert red_script.module.web_var.standard_vars["arg2"] == 123
        assert red_script.module.web_var.advanced_vars["adv_arg1"] == "advancedvalue"
        assert red_script.module.web_var.advanced_vars["adv_arg2"] == ""

    def test_reduction_script_replace_variables_when_web_var_is_dict(self):
        """
        Test that replace variables properly replaces the web_var dictionary in the module
        when the web_var attribute is a dictionary that's been pre-made by the user
        """
        test_string = 'web_var={}\nprint(123)'
        with self._test_module(test_string) as red_script:
            red_script.replace_variables(self.reduction_arguments)
            assert red_script.text() == test_string

        assert red_script.module.web_var.standard_vars["arg1"] == "somevalue"
        assert red_script.module.web_var.standard_vars["arg2"] == 123
        assert red_script.module.web_var.advanced_vars["adv_arg1"] == "advancedvalue"
        assert red_script.module.web_var.advanced_vars["adv_arg2"] == ""

    @patch(f"{REDUCTION_SERVICE_DIR}.channels_redirected")
    def test_reduce(self, _):
        """
        Test: Reduce goes through with no exceptions
        """
        self.script.skipped_runs = []
        self.script.run.return_value = None
        reduction_log_stream = io.StringIO()
        reduce(self.reduction_dir, self.temp_dir, self.datafile, self.script, self.reduction_arguments,
               reduction_log_stream)
        self.reduction_dir.create.assert_called_once()
        self.script.load.assert_called_once()
        self.temp_dir.copy.assert_called_once_with(self.reduction_dir.path)
        self.temp_dir.delete.assert_called_once()

    @patch(f"{REDUCTION_SERVICE_DIR}.channels_redirected")
    def test_reduce_script_copies_to_additional_output(self, _):
        """
        Test: Copy called on additional outputs
        When: Script returns additional output directories
        """
        self.script.skipped_runs = []
        self.script.run.return_value = "some/path"
        reduction_log_stream = io.StringIO()
        reduce(self.reduction_dir, self.temp_dir, self.datafile, self.script, self.reduction_arguments,
               reduction_log_stream)
        self.reduction_dir.create.assert_called_once()
        self.script.load.assert_called_once()
        self.temp_dir.copy.assert_has_calls([call(self.reduction_dir.path), call("some/path")])
        self.temp_dir.delete.assert_called_once()

    @patch(f"{REDUCTION_SERVICE_DIR}.open")
    @patch(f"{REDUCTION_SERVICE_DIR}.channels_redirected")
    @patch(f"{REDUCTION_SERVICE_DIR}.traceback")
    def test_reduce_script_exception_raises_script_error_and_writes_to_log(self, mock_traceback, _, mock_open):
        """
        Test: ReductionScriptError raised and script out written to
        When: Exception in reduction script
        """
        self.script.skipped_runs = []
        self.script.run.side_effect = Exception
        file = mock_open.return_value
        reduction_log_stream = io.StringIO()
        with self.assertRaises(ReductionScriptError):
            reduce(self.reduction_dir, self.temp_dir, self.datafile, self.script, self.reduction_arguments,
                   reduction_log_stream)
            file.writelines.assert_called_once()
            mock_traceback.format_exc.assert_called_once()
            file.write.assert_called_once()
            self.temp_dir.copy.assert_called_once_with(self.reduction_dir.path)

    @patch(f"{REDUCTION_SERVICE_DIR}.CEPH_DIRECTORY",
           new_callable=PropertyMock(return_value="/instrument/%s/RBNumber/RB%s/autoreduced/%s"))
    def test_reduction_directory_build_path_flat_output_removes_run_number(self, _):
        """
        Tests: Run number is removed from path
        When: _build_path is called for flat output instrument
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number, 123, flat_output=True)
        expected = Path(f"/instrument/{self.instrument}/RBNumber/RB{self.rb_number}/autoreduced")
        self.assertEqual(expected, reduction_dir.path)

    def test_reduction_directory_build_path_non_flat_builds_path(self):
        """
        Tests: _append_run_version is called
        When: _build_path is called for non flat output instrument
        """
        expected_run_version = 123
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number, expected_run_version)
        expected = Path(CEPH_DIRECTORY %
                        (self.instrument, self.rb_number, self.run_number)) / f"run-version-{expected_run_version}"
        self.assertEqual(expected, reduction_dir.path)


def fill_mockup_directory(directory):
    """
    Populates the given TemporaryDirectory object with folder and files
    :param directory: (TemporaryDirectory) The folder to be populated
    """
    (directory / "myfile.nxs").touch()
    (directory / "reduction_log").mkdir()
    (directory / "reduction_log" / "script.out").touch()
