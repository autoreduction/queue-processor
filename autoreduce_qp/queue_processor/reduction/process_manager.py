# ############################################################################ #
# Autoreduction Repository :
# https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
import logging
import os
import tempfile
from pathlib import Path
import traceback
import docker

from autoreduce_utils.settings import PROJECT_DEV_ROOT
from autoreduce_utils.message.message import Message

logger = logging.getLogger(__file__)


class ReductionProcessManager:
    def __init__(self, message: Message, run_name: str) -> None:
        self.message: Message = message
        self.run_name = run_name

    def run(self) -> Message:
        """Run the reduction subprocess."""
        try:
            temp_dir = tempfile.TemporaryDirectory()
            os.chmod(temp_dir.name, 0o777)
            with open(f'{temp_dir.name}/output.txt', "w") as out_file:
                out_file.write("Output goes here")
            os.chmod(f'{temp_dir.name}/output.txt', 0o777)
            # We need to run the reduction in a new process, otherwise scripts
            # will fail when they use things that require access to a main loop
            # e.g. a GUI main loop, for matplotlib or Mantid
            serialized_vars = self.message.serialize()
            serialized_vars_truncated = self.message.serialize(limit_reduction_script=True)
            args = ["python3", "runner.py", serialized_vars, self.run_name]
            logger.info("Calling: %s %s %s %s ", "python3", "runner.py", serialized_vars_truncated, self.run_name)

            # Return a client configured from environment variables
            # The environment variables used are the same as those used by the Docker command-line client
            # https://docs.docker.com/engine/reference/commandline/cli/#environment-variables
            client = docker.from_env()

            # Create a container and run it. Equivalent to docker run.
            # To get runner-mantid image, run:
            # docker build -t runner-mantid .

            image = client.images.pull('ghcr.io/autoreduction/runner-mantid:6.2.0')

            container = client.containers.create(
                image=image,
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
                    },
                    temp_dir.name: {
                        'bind': '/output/',
                        'mode': 'rw'
                    },
                },
                tty=True,
                environment=["AUTOREDUCTION_PRODUCTION=1"],
                stdin_open=True,
                detach=True,
            )

            container.start()
            result = container.exec_run(cmd=args)
            container.stop()

            with open(f'{temp_dir.name}/output.txt', 'r') as f:
                result_message_raw = f.read()

            container.remove()

            result_message = Message()

            result_message.populate(result_message_raw)
            temp_dir.cleanup()

        # If the specified image does not exist.
        except docker.errors.ImageNotFound as exc:
            raise exc
        # If the server returns an error.
        except docker.errors.APIError as exc:
            raise exc
        # If the container exits with a non-zero exit code and detach is False.
        except docker.errors.ContainerError as exc:
            raise exc
        except Exception:
            logger.error("Processing encountered an error: %s", traceback.format_exc())
            self.message.message = f"Processing encountered an error: {traceback.format_exc()}"
            result_message = self.message

        return result_message
