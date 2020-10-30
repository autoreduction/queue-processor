# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mock import patch, MagicMock

from queue_processors.autoreduction_processor.reduction_exceptions import DatafileError
from queue_processors.autoreduction_processor.reduction_service import ReductionDirectory, \
    TemporaryReductionDirectory, Datafile, ReductionScript
from queue_processors.autoreduction_processor.settings import MISC

REDUCTION_SERVICE_DIR = "queue_processors.autoreduction_processor.reduction_service"


class TestReductionService(unittest.TestCase):

    def setUp(self) -> None:
        patch(f"{REDUCTION_SERVICE_DIR}.LOGGER")
        self.instrument = "testinstrument"
        self.run_number = "123"
        self.rb_number = "1234"
        self.datafile = MagicMock()
        self.script = MagicMock()

    @patch(f"{REDUCTION_SERVICE_DIR}.ReductionDirectory._build_path")
    def test_reduction_directory_init_(self, mock_build):
        """
        Test: correct fields setup
        When: Object is created
        """
        reduction_dir = ReductionDirectory(self.instrument, self.rb_number, self.run_number)
        expected_path = Path(
            MISC["ceph_directory"] % (self.instrument, self.rb_number, self.run_number))
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

    @patch(f"{REDUCTION_SERVICE_DIR}.MISC")
    def test_reduction_directory_build_path_flat_output_removes_run_number(self, mock_misc):
        """
        Tests: Run number is removed from path
        When: _build_path is called for flat output instrument
        """
        d = {
            "flat_output_instruments": [self.instrument],
            "ceph_directory": "/instrument/%s/RBNumber/RB%s/autoreduced/%s"
        }
        mock_misc.__getitem__.side_effect = d.__getitem__
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
        expected = Path(
            f"/instrument/{self.instrument}/"
            f"RBNumber/RB{self.rb_number}/autoreduced/{self.run_number}")
        self.assertEqual(expected, reduction_dir.path)

    def test_reduction_directory_append_run_version_overwrite_true(self):
        """
        Tests: run-version-0 is appended
        When: overwrite is True
        """
        reduction_dir = ReductionDirectory(self.instrument,
                                           self.rb_number,
                                           self.run_number,
                                           overwrite=True)
        with TemporaryDirectory() as directory:
            reduction_dir.path = Path(directory)
            reduction_dir._append_run_version()
            (Path(directory) / "run-version-1").mkdir()
            expected_path = Path(directory) / "run-version-0"
            self.assertEqual(expected_path, reduction_dir.path)

    @patch(f"{REDUCTION_SERVICE_DIR}.MISC")
    def test_reduction_directory_append_run_version_existing_version(self, mock_misc):
        """
        Tests: Correct run-version appened
        When: a run-version already exists
        """
        with TemporaryDirectory() as directory:
            # We need to do this MISC mocking to allow string formatting in the __init__
            d = {
                "flat_output_instruments": [self.instrument],
                "ceph_directory": directory + "/%s/%s/%s"
            }
            mock_misc.__getitem__.side_effect = d.__getitem__
            reduction_dir = ReductionDirectory(self.instrument,
                                               self.rb_number,
                                               self.run_number)
            reduction_dir.path = Path(directory)
            (reduction_dir.path / "run-version-0").mkdir()
            reduction_dir._append_run_version()
            expected_path = Path(directory) / "run-version-1"
            self.assertEqual(expected_path, reduction_dir.path)

    @patch(f"{REDUCTION_SERVICE_DIR}.MISC")
    def test_reduction_directory_append_run_version_no_existing_version(self, mock_misc):
        """
        Tests: run-version-0 is appended
        When: No versions currently exist
        """
        with TemporaryDirectory() as directory:
            # We need to do this MISC mocking to allow string formatting in the __init__
            d = {
                "flat_output_instruments": [self.instrument],
                "ceph_directory": directory + "/%s/%s/%s"
            }
            mock_misc.__getitem__.side_effect = d.__getitem__
            reduction_dir = ReductionDirectory(self.instrument,
                                               self.rb_number,
                                               self.run_number)
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
        self.assertEqual(f"RB_{self.rb_number}_Run_{self.run_number}_Mantid.log",
                         temp_dir.mantid_log.name)
        self.assertEqual(f"RB_{self.rb_number}_Run_{self.run_number}_Script.out",
                         temp_dir.script_log.name)
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
            temp_reduction_dir = TemporaryReductionDirectory(self.instrument,
                                                             self.rb_number)
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
        self.assertEqual(Path(MISC["scripts_directory"] % self.instrument) / "reduce.py",
                         script.script_path)
        self.assertEqual([], script.skipped_runs)
        self.assertIsNone(script.script)

    @patch(f"{REDUCTION_SERVICE_DIR}.spec_from_file_location")
    @patch(f"{REDUCTION_SERVICE_DIR}.module_from_spec")
    def test_reduction_script_load_with_skipped_runs(self, mock_module_from_spec,
                                                     mock_spec_from_file):
        """
        Tests: Reduction script should attempt to be loaded
        When: Load is called
        """
        module_mock = MagicMock()
        mock_spec_from_file.return_value = MagicMock()
        mock_module_from_spec.return_value = module_mock
        module_mock.SKIP_RUNS = ["123"]
        script = ReductionScript(self.instrument)

        script.load()
        self.assertEqual(["123"], script.skipped_runs)
        mock_spec_from_file.assert_called_once_with("reducescript", script.script_path)
        mock_module_from_spec.assert_called_once_with(mock_spec_from_file.return_value)

    @patch(f"{REDUCTION_SERVICE_DIR}.spec_from_file_location")
    @patch(f"{REDUCTION_SERVICE_DIR}.module_from_spec")
    def test_reduction_script_load_no_skip_runs(self, mock_module_from_spec, mock_spec_from_file):
        module_mock = MagicMock()
        mock_spec_from_file.return_value = MagicMock()
        mock_module_from_spec.return_value = module_mock
        module_mock.SKIP_RUNS.side_effect = Exception
        script = ReductionScript(self.instrument)
        script.load()
        mock_spec_from_file.assert_called_once_with("reducescript", script.script_path)
        mock_module_from_spec.assert_called_once_with(mock_spec_from_file.return_value)

      
def fill_mockup_directory(directory):
    """
    Populates the given TemporaryDirectory object with folder and files
    :param directory: (TemporaryDirectory) The folder to be populated
    """
    (directory / "myfile.nxs").touch()
    (directory / "reduction_log").mkdir()
    (directory / "reduction_log" / "script.out").touch()
