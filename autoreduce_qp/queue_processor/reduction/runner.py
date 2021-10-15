# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# !/usr/bin/env python
# pylint: disable=broad-except

import io
import logging
import sys
import traceback

from autoreduce_utils.message.message import Message
from autoreduce_utils.settings import MANTID_PATH, TEMP_ROOT_DIRECTORY
from autoreduce_qp.queue_processor.reduction.exceptions import DatafileError, ReductionScriptError
from autoreduce_qp.queue_processor.reduction.utilities import windows_to_linux_path
from autoreduce_qp.queue_processor.reduction.service import (Datafile, ReductionDirectory, ReductionScript,
                                                             TemporaryReductionDirectory, reduce)

logger = logging.getLogger(__package__)


class ReductionRunner:
    """ Main class for the ReductionRunner """
    def __init__(self, message: Message, run_name: str):
        self.message = message
        self.admin_log_stream = io.StringIO()
        self.run_name = run_name
        self.data_file = windows_to_linux_path(message.data, TEMP_ROOT_DIRECTORY)
        self.facility = message.facility
        self.instrument = message.instrument
        self.proposal = message.rb_number
        self.run_number = message.run_number
        self.run_version = message.run_version
        self.reduction_arguments = message.reduction_arguments

    def reduce(self):
        """Start the reduction job."""
        self._do_reduce()
        self.message.admin_log = self.admin_log_stream.getvalue()

    def _do_reduce(self):
        """Actually do the reduction job."""
        self.message.software = self._get_mantid_version()
        if self.message.description is not None:
            logger.info("DESCRIPTION: %s", self.message.description)

        # Attempt to read the datafile
        try:
            if isinstance(self.data_file, str):
                datafiles = [Datafile(self.data_file)]
            elif isinstance(self.data_file, list):
                datafiles = [Datafile(df) for df in self.data_file]
        except DatafileError as err:
            logger.error("Problem reading datafile: %s", traceback.format_exc())
            self.message.message = "Error encountered when trying to access the datafile %s" % self.data_file
            self.message.reduction_log = "Exception:\n%s" % (err)
            return  # stops the reduction and allows the parent to read the outcome in the message

        # Attempt to read the reduction script. This does not currently respect
        # any script passed in the message https://autoreduce.atlassian.net/browse/AR-1056
        try:
            reduction_script = ReductionScript(self.instrument)
            reduction_script_path = reduction_script.script_path
        except Exception as err:
            self.message.message = "Error encountered when trying to read the reduction script"
            self.message.reduction_log = "Exception:\n%s" % (err)
            return  # stops the reduction and allows the parent to read the outcome in the message

        # Attempt to open the reduction directory
        try:
            reduction_dir = ReductionDirectory(self.instrument,
                                               self.proposal,
                                               self.run_name,
                                               self.run_version,
                                               flat_output=self.message.flat_output)
            temp_dir = TemporaryReductionDirectory(self.proposal, self.run_name)
        except Exception as err:
            self.message.message = "Error encountered when trying to read the reduction directory"
            self.message.reduction_log = "Exception:\n%s" % (err)
            return  # stops the reduction and allows the parent to read the outcome in the message

        reduction_log_stream = io.StringIO()
        try:
            reduce(reduction_dir, temp_dir, datafiles, reduction_script, self.reduction_arguments, reduction_log_stream)
            self.message.reduction_log = reduction_log_stream.getvalue()
            self.message.reduction_data = str(reduction_dir.path)
        except ReductionScriptError as err:
            logger.error("Reduction script path: %s", reduction_script_path)
            self.message.message = "Error encountered when running the reduction script"
            self.message.reduction_log = "Exception:\n%s\n\n%s\n\n## Script output ##\n%s" % (
                reduction_script_path, err, reduction_log_stream.getvalue())
        except Exception as err:
            logger.error(traceback.format_exc())
            self.message.message = "REDUCTION Error: %s" % err

    @staticmethod
    def _get_mantid_version():
        """
        Attempt to get Mantid software version
        :return: (str) Mantid version or None if not found
        """
        if MANTID_PATH not in sys.path:
            sys.path.append(MANTID_PATH)
        try:
            # pylint:disable=import-outside-toplevel
            import mantid
            return mantid.__version__
        except ImportError as excep:
            logger.error("Unable to discover Mantid version as: unable to import Mantid")
            logger.error(excep)
        return None


def main():
    """
    This is the entrypoint when a reduction is started. This is run in a subprocess from
    ReductionProcessManager, and the required parameters to perform the reduction are passed
    as process arguments.

    Additionally, the resulting Message is written to a temporary file which the
    parent process reads back to mark the result of the reduction run in the DB.
    """
    data, temp_output_file, run_name = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        message = Message()
        message.populate(data)
    except ValueError as exp:
        logger.error("Could not populate message from data: %s", str(exp))
        raise

    try:
        reduction = ReductionRunner(message, run_name)
    except Exception as exp:
        message.message = str(exp)
        logger.info("Message data error: %s", message.serialize(limit_reduction_script=True))
        raise

    log_stream_handler = logging.StreamHandler(reduction.admin_log_stream)
    logger.addHandler(log_stream_handler)
    try:
        reduction.reduce()
        # write out the reduction message
        with open(temp_output_file, "w") as out_file:
            out_file.write(reduction.message.serialize())

    except Exception as exp:
        logger.info("ReductionRunner error: %s", str(exp))
        raise

    finally:
        logger.removeHandler(log_stream_handler)


if __name__ == "__main__":  # pragma : no cover
    main()
