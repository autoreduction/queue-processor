# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Reduction service contains the classes, and functions that performs a reduction
"""
import io
import logging
import os
import traceback
import types
from distutils.dir_util import copy_tree
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from autoreduce_utils.settings import SCRIPTS_DIRECTORY, CEPH_DIRECTORY, SCRIPT_TIMEOUT

from autoreduce_qp.queue_processor.reduction.exceptions import DatafileError, ReductionScriptError
from autoreduce_qp.queue_processor.reduction.timeout import TimeOut
from autoreduce_qp.queue_processor.reduction.utilities import channels_redirected

logger = logging.getLogger(__package__)


class ReductionDirectory:
    """
    ReductionDirectory encapsulated directory creation, deletion and handling output type
    (flat or not)
    """
    def __init__(self, instrument, rb_number, run_name, run_version, flat_output=False):
        self._is_flat_directory = flat_output
        self.run_version = run_version
        self.path = Path(CEPH_DIRECTORY % (instrument, rb_number, run_name))
        if self._is_flat_directory:
            self.path = self.path.parent
        else:
            self.path = self.path / f"run-version-{self.run_version}"

        self.log_path = self.path / "reduction_log"
        self.mantid_log = self.log_path / f"RB_{rb_number}_Run_{run_name}_Mantid.log"
        self.script_log = self.log_path / f"RB_{rb_number}_Run_{run_name}_Script.out"

    def create(self):
        """
        Creates the reduction directory including the log path, Script.out and Mantid.log files
        """
        logger.info("Creating reduction directory: %s", self.path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(exist_ok=True)
        self.script_log.touch(exist_ok=True)
        self.mantid_log.touch(exist_ok=True)


class TemporaryReductionDirectory:
    """
    Encapsulates the use of the temporary reduction directory
    """
    def __init__(self, rb_number, run_name):
        self._temp_dir = TemporaryDirectory()  # pylint:disable=consider-using-with
        self._path = Path(self._temp_dir.name)
        self.log_path = self._path / "reduction_log"
        self.mantid_log = self.log_path / f"RB_{rb_number}_Run_{run_name}_Mantid.log"
        self.script_log = self.log_path / f"RB_{rb_number}_Run_{run_name}_Script.out"
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

    def copy(self, destination: Path):
        """
        Copy the contents of the temporary directory to the given destination, overwriting what is
        already present.
        :param destination: (Path like) the copy destination
        """
        logger.info("Copying %s to %s", self.path, destination)
        copy_tree(self.path, str(destination))  # We have to convert path objects to str

    @property
    def path(self) -> str:
        """
        Returns the path string with a slash at the end. This is because some reduction scripts just do
        `output_dir + str` resulting in broken output copying, as all output files end up being /tmp/abcedfgFILENAME.nxs
        rather than /tmp/abcedfg/FILENAME.nxs
        """
        return f"{self._path}/"

    def exists(self) -> bool:
        """Checks that the path for the TemporaryReductionDirectory exists"""
        return self._path.exists()


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
    def __init__(self, instrument, module="reduce.py"):
        self.script_path: Path = Path(SCRIPTS_DIRECTORY % instrument) / module
        self.skipped_runs = []
        self.module = None

    def exists(self) -> bool:
        """
        Returns whether the script file exists
        """
        return self.script_path.exists()

    def load(self):
        """
        Loads the reduction script as a module
        :raises ImportError: If the reduction script is missing an import
        :raises SyntaxError: If there is a syntax error in the reduction script
        """

        module_name = os.path.splitext(self.script_path.name)[0]
        try:
            spec = spec_from_file_location(module_name, self.script_path)
            if spec is None:
                raise ImportError(f"Module at {self.script_path} does not exist.")
            self.module = module_from_spec(spec)
            spec.loader.exec_module(self.module)
            return self.module
        except ImportError as exp:
            logger.error("Unable to load reduction script %s due to missing import. (%s)", self.script_path, exp)
            raise
        except SyntaxError:
            logger.error("Syntax error in reduction script %s", self.script_path)
            raise

    def text(self) -> str:
        """Returns the text of the script file. Does not load it as a module"""
        # Read raw bytes and determine encoding
        try:
            with io.open(self.script_path, 'r') as open_file:
                return open_file.read()
        except IOError:
            return ""

    def replace_variables(self, reduction_arguments):
        """
        We mock up the web_var module according to what's expected. The scripts want standard_vars
        and advanced_vars, e.g.
        https://github.com/mantidproject/mantid/blob/master/scripts/Inelastic/Direct/ReductionWrapper.py
        """
        def merge_dicts(dict_name):
            """
            Merge self.reduction_arguments[dictName] into reduce_script.web_var[dictName],
            overwriting any key that exists in both with the value from sourceDict.
            """
            def merge_dict_to_name(source_dict):
                """ Merge the two dictionaries. """
                old_dict = {}
                if hasattr(self.module.web_var, dict_name):
                    old_dict = getattr(self.module.web_var, dict_name)
                else:
                    pass
                old_dict.update(source_dict)
                setattr(self.module.web_var, dict_name, old_dict)

            def ascii_encode(var):
                """ ASCII encode var. """
                return var.encode('ascii', 'ignore') if type(var).__name__ == "unicode" else var

            encoded_dict = {k: ascii_encode(v) for k, v in reduction_arguments[dict_name].items()}
            merge_dict_to_name(encoded_dict)

        if not self.module:
            raise RuntimeError("The script has not been loaded yet")

        self.module.web_var = types.ModuleType("reduce_vars")
        merge_dicts("standard_vars")
        merge_dicts("advanced_vars")

    def run(self, input_files: List[Datafile], output_dir):
        """
        Runs the reduction script on the given input file and outputs to the given
        ReductionReturn and returns the return value of the main function of the script.
        :param input_file: (Datafile) Input datafile
        :param output_dir: (ReductionDirectory) Directory to output to
        :return:
        """
        logger.info("Running reduction script: %s", self.script_path)
        final_input_files = str(
            input_files[0].path) if len(input_files) == 1 else [in_file.path for in_file in input_files]
        with TimeOut(SCRIPT_TIMEOUT):
            return self.module.main(input_file=final_input_files, output_dir=str(output_dir.path))


def reduce(reduction_dir, temp_dir, datafiles: List[Datafile], script, reduction_arguments, log_stream):
    """
    Performs a reduction on the given datafile using the given script, outputting to the given
    output directory
    :param reduction_dir: (ReductionDirectory) The final directory to output to
    :param temp_dir: (TemporaryReductionDirectory) Where the reduction initially outputs to
    :param datafile: (Datafile) The datafile to perform the reduction on
    :param script: (ReductionScript) The Script used to reduce the data
    :param log_stream: (StringIO) A stream to which the log output will be written
    :return (StringIO): The log stream of the reduction script
    """
    reduction_dir.create()
    logger.info("-------------------------------------------------------")
    logger.info("Temporary result directory: %s", temp_dir.path)
    logger.info("Final Result directory: %s", reduction_dir.path)
    logger.info("Temporary log dir: %s", temp_dir.log_path)
    logger.info("Final log dir: %s", reduction_dir.log_path)
    logger.info("Datafile: %s", [datafile.path for datafile in datafiles])
    logger.info("Reduction script: %s", script.script_path)
    logger.info("-------------------------------------------------------")
    logger.info("Starting reduction...")

    log_stream_handler = logging.StreamHandler(log_stream)
    logger.addHandler(log_stream_handler)

    try:
        script.load()
        script.replace_variables(reduction_arguments)
        with channels_redirected(temp_dir.script_log, temp_dir.mantid_log, log_stream):
            additional_output_dirs = script.run(datafiles, temp_dir)
        logger.removeHandler(log_stream_handler)
    except Exception as ex:
        logger.error("Exception caught in reduction script. Traceback is logged below:")
        logger.error(traceback.format_exc())
        with open(temp_dir.script_log, "a") as target:
            target.writelines(str(ex) + "\n")
            target.write(traceback.format_exc())
        raise ReductionScriptError("Exception in reduction script", ex) from ex
    finally:
        temp_dir.copy(reduction_dir.path)

    if additional_output_dirs:
        temp_dir.copy(additional_output_dirs)

    temp_dir.delete()
    return log_stream
