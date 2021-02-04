# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module that reads from the reduction pending queue and calls the python script on that data.
"""
import logging
import os
import subprocess
import sys
import tempfile
import traceback

from model.message.message import Message

REDUCTION_DIRECTORY = f"{os.path.dirname(os.path.realpath(__file__))}/runner.py"


class ReductionProcessManager:
    def __init__(self, message: Message) -> None:
        self.message: Message = message

    def run(self) -> Message:
        """
        Runs the reduction process
        """
        try:
            # We need to run the reduction in a new process, otherwise scripts
            # will fail when they use things that require access to a main loop
            # e.g. a GUI main loop, for matplotlib or Mantid
            python_path = sys.executable
            with tempfile.NamedTemporaryFile("w+") as temp_output_file:
                args = [python_path, REDUCTION_DIRECTORY, self.message.serialize(), temp_output_file.name]
                logging.info("Calling: %s %s %s %s", python_path, REDUCTION_DIRECTORY,
                             self.message.serialize(limit_reduction_script=True), temp_output_file.name)
                subprocess.run(args, check=True)
                result_message_raw = temp_output_file.file.read()

            result_message = Message()
            result_message.populate(result_message_raw)
        except subprocess.CalledProcessError:
            logging.error("Processing encountered an error: %s", traceback.format_exc())
            self.message.message = f"Processing encountered an error: {traceback.format_exc()}"
            result_message = self.message

        return result_message
