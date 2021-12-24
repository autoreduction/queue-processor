# ############################################################################ #
# Autoreduction Repository :
# https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
import logging
import os
import subprocess
import sys
import tempfile
import traceback

from autoreduce_utils.message.message import Message

RUNNER_PATH = f"{os.path.dirname(os.path.realpath(__file__))}/runner.py"

logger = logging.getLogger(__file__)


class ReductionProcessManager:
    def __init__(self, message: Message, run_name: str) -> None:
        self.message: Message = message
        self.run_name = run_name

    def run(self) -> Message:
        """Run the reduction subprocess."""
        try:
            # We need to run the reduction in a new process, otherwise scripts
            # will fail when they use things that require access to a main loop
            # e.g. a GUI main loop, for matplotlib or Mantid
            python_path = sys.executable
            with tempfile.NamedTemporaryFile("w+") as temp_output_file:
                args = [python_path, RUNNER_PATH, self.message.serialize(), temp_output_file.name, self.run_name]
                logger.info("Calling: %s %s %s %s %s", python_path, RUNNER_PATH,
                            self.message.serialize(limit_reduction_script=True), temp_output_file.name, self.run_name)

                # Copy and update the subprocess environment to inherit the
                # parent one, and append the PYTHONPATH of the queue_processor module
                environment = os.environ.copy()

                pythonpath = environment.get("PYTHONPATH", "")
                pythonpath += f':{RUNNER_PATH.split("autoreduce_qp")[0]}'
                pythonpath = environment["PYTHONPATH"] = pythonpath

                # Run process until finished and check the exit code for success
                subprocess.run(args, check=True, env=environment)

                # The subprocess will write out the result message in the
                # tempfile, read it back
                result_message_raw = temp_output_file.file.read()

            result_message = Message()
            result_message.populate(result_message_raw)
        except subprocess.CalledProcessError:
            logger.error("Processing encountered an error: %s", traceback.format_exc())
            self.message.message = f"Processing encountered an error: {traceback.format_exc()}"
            result_message = self.message

        return result_message
