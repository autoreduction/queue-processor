# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Reduction service contains the classes, and functions that performs a reduction
"""
import logging
import os
import time
import traceback
from distutils.dir_util import copy_tree
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from tempfile import TemporaryDirectory

from queue_processors.autoreduction_processor.post_process_admin_utilities import \
    channels_redirected
from queue_processors.autoreduction_processor.reduction_exceptions import DatafileError, \
    SkippedRunException, \
    ReductionScriptError
from queue_processors.autoreduction_processor.settings import MISC
from queue_processors.autoreduction_processor.timeout import TimeOut

LOGGER = logging.getLogger(__file__)


class ReductionDirectory:
    """
    ReductionDirectory encapsulated directory creation, deletion and handling output type
    (flat or not)
    """

    def __init__(self, instrument, rb_number, run_number, overwrite=False):
        self.overwrite = overwrite
        self._is_flat_directory = instrument in MISC["flat_output_instruments"]
        self.path = Path(
            MISC["ceph_directory"] % (instrument, rb_number, run_number))
        self._build_path()
        self.log_path = self.path / "reduction_log"
        self.mantid_log = self.log_path / f"RB_{rb_number}_Run_{run_number}_Mantid.log"
        self.script_log = self.log_path / f"RB_{rb_number}_Run_{run_number}_Script.out"

    def create(self):
        """
        Creates the reduction directory including the log path, Script.out and Mantid.log files
        """
        LOGGER.info("Creating reduction directory: %s", self.path)
        self.path.mkdir(parents=True)
        self.log_path.mkdir()
        self.script_log.touch()
        self.mantid_log.touch()

    def delete(self):
        """
        Delete the Reduction directory and all of its contents recursively
        """
        LOGGER.info("Deleting directory: %s", self.path)
        for sleep in [0, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
            self._rm_tree(self.path)
            if not self.path.exists():
                break
            time.sleep(sleep)
        else:
            LOGGER.warning("Failed to delete %s", self.path)

    def _rm_tree(self, path):
        for child in path.glob("*"):
            if child.is_file():
                try:
                    child.unlink()
                except FileNotFoundError:
                    pass
            else:
                self._rm_tree(child)
        path.rmdir()

    def _build_path(self):
        if self._is_flat_directory:
            self.path = self.path.parent
        else:
            self._append_run_version()

    def _append_run_version(self):
        if self.overwrite:
            self.path = self.path / "run-version-0"
        else:
            versions = [int(str(i).split("-")[-1])
                        for i in self.path.glob("run-version-[0-9]*") if i.is_dir()]
            try:
                self.path = self.path / f"run-version-{max(versions) + 1}"
            except ValueError:
                self.path = self.path / "run-version-0"


class TemporaryReductionDirectory:
    """
    Encapsulates the use of the temporary reduction directory
    """

    def __init__(self, rb_number, run_number):
        self._temp_dir = TemporaryDirectory()
        self.path = Path(self._temp_dir.name)
        self.log_path = self.path / "reduction_log"
        self.mantid_log = self.log_path / f"RB_{rb_number}_Run_{run_number}_Mantid.log"
        self.script_log = self.log_path / f"RB_{rb_number}_Run_{run_number}_Script.out"
        self._create()

    def _create(self):
        self.log_path.mkdir()
        self.mantid_log.touch()
        self.script_log.touch()

    def delete(self):
        """
        Deletes the temporary directory and all of its contents.
        """
        self._temp_dir.cleanup()

    def copy(self, destination):
        """
        Copy the contents of the temporary directory to the given destination, overwriting what is
        already present.
        :param destination: (Path like) the copy destination
        """
        LOGGER.info("Copying %s to %s", self.path, destination)
        copy_tree(self.path, str(destination))  # We have to convert path objects to str


# pylint:disable=too-few-public-methods; As pylint does not like value objects
class Datafile:
    """
    Encapsulates datafile path and verification
    """

    def __init__(self, path):
        self.path = Path(path)
        try:
            assert os.access(path, os.R_OK)
        except AssertionError as ex:
            raise DatafileError(f"Problem reading datafile: {path}") from ex


class ReductionScript:
    """
    Encapsulates the loading and running of a reduction script
    """

    def __init__(self, instrument):
        self.script_path = Path(MISC["scripts_directory"] % instrument) / "reduce.py"
        self.skipped_runs = []
        self.script = None

    def load(self):
        """
        Loads the reduction script as a module and stores any run numbers that are to be skipped
        by the script
        """
        spec = spec_from_file_location("reducescript", self.script_path)
        self.script = module_from_spec(spec)
        spec.loader.exec_module(self.script)
        try:
            self.skipped_runs = self.script.SKIP_RUNS
        except:  # pylint:disable=bare-except
            pass

    def run(self, input_file, output_dir):
        """
        Runs the reduction script on the given input file and outputs to the given
        ReductionReturn and returns the return value of the main function of the script.
        :param input_file: (Datafile) Input datafile
        :param output_dir: (ReductionDirectory) Directory to output to
        :return:
        """
        LOGGER.info("Running reduction script: %s", self.script_path)
        with TimeOut(MISC["script_timeout"]):
            return self.script.main(input_file=input_file, output_dir=output_dir)

# pylint:disable=too-many-arguments; We will remove the log_Stream once we look at logging in ppa
# more closely
def reduce(reduction_dir, temp_dir, datafile, script, run_number, log_stream):
    """
    Performs a reduction on the given datafile using the given script, outputting to the given
    output directory
    :param reduction_dir: (ReductionDirectory) The final directory to output to
    :param temp_dir: (TemporaryReductionDirectory) Where the reduction initially outputs to
    :param datafile: (Datafile) The datafile to perform the reduction on
    :param script: (ReductionScript) The Script used to reduce the data
    :param run_number: (String) The run number of this reduction
    :param log_stream: (StringIO) The logstream to redirect the reduction logs to.
    """
    reduction_dir.create()
    LOGGER.info("-------------------------------------------------------")
    LOGGER.info("Temporary result directory: %s", temp_dir.path)
    LOGGER.info("Final Result directory: %s", reduction_dir.path)
    LOGGER.info("Temporary log dir: %s", temp_dir.log_path)
    LOGGER.info("Final log dir: %s", reduction_dir.log_path)
    LOGGER.info("Datafile: %s", datafile.path)
    LOGGER.info("Reduction script: %s", script.script_path)
    LOGGER.info("-------------------------------------------------------")
    LOGGER.info("Starting reduction...")

    with channels_redirected(temp_dir.script_log,
                             temp_dir.mantid_log,
                             log_stream):
        script.load()
        if run_number in script.skipped_runs:
            raise SkippedRunException("Run has been skipped in script")

        try:
            additional_output_dirs = script.run(datafile.path, temp_dir.path)
        except Exception as ex:
            LOGGER.error("exception caught in reduction script")
            LOGGER.error(traceback.format_exc())
            with open(temp_dir.script_log(), "a") as target:
                target.writelines(str(ex) + "\n")
                target.write(traceback.format_exc())
            raise ReductionScriptError("Exception in reduction script", ex) from ex
        finally:
            temp_dir.copy(reduction_dir.path)

        if additional_output_dirs:
            temp_dir.copy(additional_output_dirs)

        temp_dir.delete()
