# ############################################################################ #
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
import logging
import os
from pathlib import Path
import subprocess
import tempfile
import traceback
from autoreduce_utils.settings import CEPH_DIRECTORY
import docker

from autoreduce_utils.message.message import Message

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
            with tempfile.NamedTemporaryFile(encoding='utf-8', mode="w+") as temp_output_file:
                serialized_vars = self.message.serialize()
                serialized_vars_truncated = self.message.serialize(limit_reduction_script=True)
                args = ["python3", "runner.py", serialized_vars, temp_output_file.name, self.run_name]
                logger.info("Calling: %s %s %s %s %s", "python3", "runner.py", serialized_vars_truncated,
                            temp_output_file.name, self.run_name)

                os.environ["AUTOREDUCTION_PRODUCTION"] = "true"
                # Return a client configured from environment variables
                # The environment variables used are the same as those used by the Docker command-line client
                # https://docs.docker.com/engine/reference/commandline/cli/#environment-variables
                client = docker.from_env()

                # Create a container without starting it. Similar to docker create.
                # To get autoreduction/mantid image, run:
                # DOCKER_BUILDKIT=1 docker build -t autoreduce/mantid .
                container = client.containers.create('autoreduce/mantid',
                                                     command="/bin/sh",
                                                     volumes={
                                                         f'{os.path.expanduser("~")}/.autoreduce/': {
                                                             'bind': f'{os.path.expanduser("~")}/.autoreduce/',
                                                             'mode': 'rw'
                                                         },
                                                         f'{os.path.expanduser("~")}/.autoreduce/dev/data-archive': {
                                                             'bind': '/isis/',
                                                             'mode': 'rw'
                                                         },
                                                         f'{os.path.expanduser("~")}/.autoreduce/dev/reduced-data': {
                                                             'bind': '/instrument/',
                                                             'mode': 'rw'
                                                         }
                                                     },
                                                     tty=True,
                                                     environment=["AUTOREDUCTION_PRODUCTION=true"],
                                                     tmpfs={'/tmp': ''},
                                                     stdin_open=True,
                                                     auto_remove=False)

                # Start the container
                # Container should write out the results to the temporary file
                container.start()
                exe = container.exec_run(cmd=args)

                # Read the output from the temporary file
                expected_path = Path(CEPH_DIRECTORY % (self.instrument, self.rb_number, self.run_number))

                result_message_raw = temp_output_file.file.read()

                container.stop()

            result_message = Message()
            result_message.populate(result_message_raw)
        except subprocess.CalledProcessError:
            logger.error("Processing encountered an error: %s", traceback.format_exc())
            self.message.message = f"Processing encountered an error: {traceback.format_exc()}"
            result_message = self.message

        return result_message
