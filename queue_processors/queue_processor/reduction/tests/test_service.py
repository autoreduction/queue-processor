# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for parts of the reduction_service
"""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, PropertyMock

from mock import patch, MagicMock, call

from queue_processors.queue_processor.reduction.exceptions import DatafileError, ReductionScriptError
from queue_processors.queue_processor.reduction.service import ReductionDirectory, \
    TemporaryReductionDirectory, Datafile, ReductionScript, reduce
from queue_processors.queue_processor.settings import CEPH_DIRECTORY, SCRIPTS_DIRECTORY
from queue_processors.queue_processor.reduction.tests.module_to_import import TEST_DICTIONARY

REDUCTION_SERVICE_DIR = "queue_processors.queue_processor.reduction.service"


class TempDirPropertyMock(PropertyMock):
    def __init__(self, path_string, *args) -> None:
        super().__init__(*args)
        directory = TemporaryDirectory()
        self.return_value = directory.name + path_string


# pylint:disable=protected-access,too-many-instance-attributes


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
        self.log_stream = MagicMock()

    @patch(f"{REDUCTION_SERVICE_DIR}.ReductionDirectory._build_path")
    def test_reduction_directory_init_(self, mock_build):
        """
        Test: correct fields setup
        When: Object is created
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number)
        expected_path = Path(CEPH_DIRECTORY % (self.instrument, self.rb_number, self.run_number))
        expected_log_path = expected_path / "reduction_log"
        expected_mantid_log = expected_log_path / f"RB_{self.rb_number}_" \
                                                  f"Run_{self.run_number}_Mantid.log"
        expected_script_log = expected_log_path / f"RB_{self.rb_number}_" \
                                                  f"Run_{self.run_number}_Script.out"
        self.assertEqual(expected_path, reduction_dir.path)
        self.assertEqual(expected_log_path, reduction_dir.log_path)
        self.assertEqual(expected_mantid_log, reduction_dir.mantid_log)
        self.assertEqual(expected_script_log, reduction_dir.script_log)
        mock_build.assert_called_once()

    @patch(f"{REDUCTION_SERVICE_DIR}.Path")
    @patch(f"{REDUCTION_SERVICE_DIR}.ReductionDirectory._build_path")
    def test_reduction_directory_create(self, _, __):
        """
        Test: Directory is created
        When: create is called
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number)
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

    @patch(f"{REDUCTION_SERVICE_DIR}.FLAT_OUTPUT_INSTRUMENTS",
           new_callable=PropertyMock(return_value=["testinstrument"]))
    @patch(f"{REDUCTION_SERVICE_DIR}.CEPH_DIRECTORY",
           new_callable=PropertyMock(return_value="/instrument/%s/RBNumber/RB%s/autoreduced/%s"))
    def test_reduction_directory_build_path_flat_output_removes_run_number(self, _, __):
        """
        Tests: Run number is removed from path
        When: _build_path is called for flat output instrument
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number)
        expected = Path(f"/instrument/{self.instrument}/RBNumber/RB{self.rb_number}/autoreduced")
        self.assertEqual(expected, reduction_dir.path)

    @patch(f"{REDUCTION_SERVICE_DIR}.ReductionDirectory._append_run_version")
    def test_reduction_directory_build_path_non_flat_builds_path(self, mock_append):
        """
        Tests: _append_run_version is called
        When: _build_path is called for non flat output instrument
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number)
        mock_append.assert_called_once()
        expected = Path(CEPH_DIRECTORY % (self.instrument, self.rb_number, self.run_number))
        self.assertEqual(expected, reduction_dir.path)

    def test_reduction_directory_append_run_version_overwrite_true(self):
        """
        Tests: run-version-0 is appended
        When: overwrite is True
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number, overwrite=True)
        with TemporaryDirectory() as directory:
            reduction_dir.path = Path(directory)
            reduction_dir._append_run_version()
            (Path(directory) / "run-version-1").mkdir()
            expected_path = Path(directory) / "run-version-0"
            self.assertEqual(expected_path, reduction_dir.path)

    def test_reduction_directory_append_run_version_existing_version(self):
        """
        Tests: Correct run-version appened
        When: a run-version already exists
        """
        with TemporaryDirectory() as directory:
            reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number)
            reduction_dir.path = Path(directory)
            (reduction_dir.path / "run-version-0").mkdir()
            reduction_dir._append_run_version()
            expected_path = Path(directory) / "run-version-1"
            self.assertEqual(expected_path, reduction_dir.path)

    def test_reduction_directory_append_run_version_no_existing_version(self):
        """
        Tests: run-version-0 is appended
        When: No versions currently exist
        """
        with TemporaryDirectory() as directory:
            reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number)
            reduction_dir.path = Path(directory)
            reduction_dir._append_run_version()
            expected_path = Path(directory) / "run-version-0"
            self.assertEqual(expected_path, reduction_dir.path)

    # TempReductionDirectory Tests
    def test_temp_reduction_directory_init(self):
        """
        Tests: Temporary directory is created and populated
        When: object is created
        """
        temp_dir = TemporaryReductionDirectory(self.rb_number, self.run_number)
        self.assertTrue(temp_dir.path.exists())
        self.assertTrue(temp_dir.log_path.exists())
        self.assertTrue(temp_dir.mantid_log.exists())
        self.assertTrue(temp_dir.script_log.exists())
        self.assertEqual("reduction_log", temp_dir.log_path.name)
        self.assertEqual(f"RB_{self.rb_number}_Run_{self.run_number}_Mantid.log", temp_dir.mantid_log.name)
        self.assertEqual(f"RB_{self.rb_number}_Run_{self.run_number}_Script.out", temp_dir.script_log.name)
        temp_dir.delete()
        self.assertFalse(temp_dir.path.exists())

    def test_temp_reduction_directory_delete(self):
        """
        Tests: Temporary Directory is deleted
        When: Delete is called
        """
        temp_dir = TemporaryReductionDirectory(self.rb_number, self.rb_number)
        self.assertTrue(temp_dir.path.exists())
        temp_dir.delete()
        self.assertFalse(temp_dir.path.exists())

    def test_temporary_reduction_directory_copy(self):
        """
        Tests: Directory is copied
        When: copy is called
        """
        with TemporaryDirectory() as dest, TemporaryDirectory() as src:
            temp_reduction_dir = TemporaryReductionDirectory(self.instrument, self.rb_number)
            dest_folder = Path(dest)
            src_folder = Path(src)
            temp_reduction_dir.path = src_folder
            fill_mockup_directory(temp_reduction_dir.path)

            temp_reduction_dir.copy(dest)
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

    def test_reduction_script_run(self):
        """
        Tests: Correct fields set up
        When: reduction script object is created
        """
        script = ReductionScript(self.instrument)

        script.module = Mock()
        script.run(Datafile("/tmp"), Datafile("/tmp"))

        script.module.main.assert_called_once()

    def test_reduction_script_load(self):
        """
        Test importing a module that is all OK
        """
        red_script = ReductionScript(self.instrument)
        red_script.script_path = Path(os.path.join(os.path.dirname(__file__), "module_to_import.py"))
        module = red_script.load()

        assert getattr(module, "TEST_DICTIONARY") == TEST_DICTIONARY
        assert red_script.module is not None

    def test_reduction_script_load_invalid_module(self):
        """
        Test importing a module that does not exist
        """
        red_script = ReductionScript(self.instrument)
        red_script.script_path = Path("some.module.that.does.not.exist")
        with self.assertRaises(ImportError):
            red_script.load()

    def test_reduction_script_load_syntax_error(self):
        """
        Test importing a module that has a syntax error in it
        """
        red_script = ReductionScript(self.instrument)
        module_with_syntax_error_str = """TEST_DICTIONARY = {"key1": "value1"""
        module_path = os.path.join("/tmp", "module_with_syntax_error.py")
        red_script.script_path = Path(module_path)

        with open(module_path, 'w') as file:
            file.write(module_with_syntax_error_str)

        with self.assertRaises(SyntaxError):
            red_script.load()

        os.remove(module_path)

    @patch("io.open", side_effect=IOError)
    def test_reduction_script_text_ioerror(self, _: Mock):
        """
        Test importing a module that has a syntax error in it
        """
        red_script = ReductionScript(self.instrument)
        assert red_script.text() == ""

    def test_reduction_script_text(self):
        """
        Test importing a module that has a syntax error in it
        """
        script_file = Path("/tmp/somepath.py")
        test_string = 'print(123)'

        with open("/tmp/somepath.py", 'w') as file:
            file.write(test_string)

        red_script = ReductionScript(self.instrument)
        red_script.script_path = script_file

        assert red_script.text() == test_string

        os.remove(script_file)

    @patch(f"{REDUCTION_SERVICE_DIR}.channels_redirected")
    def test_reduce(self, _):
        """
        Test: Reduce goes through with no exceptions
        """
        self.script.skipped_runs = []
        self.script.run.return_value = None
        reduce(self.reduction_dir, self.temp_dir, self.datafile, self.script)
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
        reduce(self.reduction_dir, self.temp_dir, self.datafile, self.script)
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
        with self.assertRaises(ReductionScriptError):
            reduce(self.reduction_dir, self.temp_dir, self.datafile, self.script)
            file.writelines.assert_called_once()
            mock_traceback.format_exc.assert_called_once()
            file.write.assert_called_once()
            self.temp_dir.copy.assert_called_once_with(self.reduction_dir.path)


def fill_mockup_directory(directory):
    """
    Populates the given TemporaryDirectory object with folder and files
    :param directory: (TemporaryDirectory) The folder to be populated
    """
    (directory / "myfile.nxs").touch()
    (directory / "reduction_log").mkdir()
    (directory / "reduction_log" / "script.out").touch()
