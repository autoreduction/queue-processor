# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module that reads from the reduction pending queue and calls the python script on that data.
"""
from typing import Tuple
import os
import subprocess
import sys

import stomp

from twisted.internet import reactor

from model.message.message import Message
from queue_processors.autoreduction_processor.autoreduction_logging_setup import logger
from queue_processors.autoreduction_processor.settings import MISC
from queue_processors.autoreduction_processor.post_process_admin import PostProcessAdmin
import tempfile


class FakeClient:
    @staticmethod
    def send(amq_message, message):
        print(amq_message, message)


class ProcessingRunner:
    def __init__(self, message) -> None:
        self.message = message

    def run(self) -> Tuple[bool, Message, str]:
        if not os.path.isfile(MISC['post_process_directory']):
            logger.warning("Could not find autoreduction post processing file "
                           "- please contact a system administrator")
        python_path = sys.executable
        logger.info("Calling: %s %s %s %s", python_path, MISC['post_process_directory'],
                    self.message.serialize(limit_reduction_script=True))
        try:
            # We need to run the reduction in a new process, otherwise scripts
            # will fail when they use things that don't like being subprocesses,
            # e.g. matplotlib or Mantid
            python_path = sys.executable
            logger.info("Calling: %s %s %s %s", python_path, MISC['post_process_directory'],
                        self.message.serialize(limit_reduction_script=True))
            with tempfile.NamedTemporaryFile("w+") as temp_output_file:
                args = [
                    python_path, MISC['post_process_directory'],
                    self.message.serialize(), temp_output_file.name
                ]
                subprocess.run(args, check=True)
                result_message_raw = temp_output_file.file.read()

            result_message = Message()
            result_message.populate(result_message_raw)
            return True, result_message, ""
        except subprocess.CalledProcessError as err:
            # TODO mark script error
            logger.error("Processing encountered an error: %s", str(err))
            return False, None, err
