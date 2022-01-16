# ############################################################################ #
# Autoreduction Repository :
# https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
import logging
import os
from pathlib import Path
import tempfile
import traceback
import docker
from docker.errors import APIError, ImageNotFound, ContainerError

from autoreduce_utils.settings import ARCHIVE_ROOT, AUTOREDUCE_HOME_ROOT, PROJECT_DEV_ROOT
from autoreduce_utils.message.message import Message
from autoreduce_db.reduction_viewer.models import Software

from autoreduce_qp.queue_processor.reduction.utilities import get_correct_image

logger = logging.getLogger(__file__)


class ReductionProcessManager:

    def __init__(self, message: Message, run_name: str, software: Software) -> None:
        self.message: Message = message
        self.run_name = run_name
        self.software = software

    def run(self) -> Message:
        """Run the reduction subprocess."""
        try:
            # Create a temp directory to store reduction result
            # Volume bind for the container to write to and host to read from
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chmod(temp_dir, 0o777)

                # We need to run the reduction in a new process, otherwise scripts
                # will fail when they use things that require access to a main loop
                # e.g. a GUI main loop, for matplotlib or Mantid
                serialized_vars = self.message.serialize()
                serialized_vars_truncated = self.message.serialize(limit_reduction_script=True)
                args = ["autoreduce-runner-start", serialized_vars, self.run_name]
                logger.info("Calling: %s %s %s %s ", "python3", "runner.py", serialized_vars_truncated, self.run_name)

                # Return a client configured from environment variables
                # The environment variables used are the same as those used by the Docker command-line client
                # https://docs.docker.com/engine/reference/commandline/cli/#environment-variables
                client = docker.from_env()

                image = get_correct_image(client, self.software)

                if "AUTOREDUCTION_PRODUCTION" in os.environ:
                    reduced_data = Path('/instrument')
                else:
                    reduced_data = Path(f'{PROJECT_DEV_ROOT}/reduced-data')
                    if not os.path.exists(ARCHIVE_ROOT):
                        Path(ARCHIVE_ROOT).mkdir(parents=True, exist_ok=True)
                    if not os.path.exists(reduced_data):
                        reduced_data.mkdir(parents=True, exist_ok=True)

                    # Run chmod's to make sure the directories are writable
                    reduced_data.chmod(0o777)
                    Path(ARCHIVE_ROOT).chmod(0o777)
                    Path(f'{AUTOREDUCE_HOME_ROOT}/logs/autoreduce.log').chmod(0o777)

                container = client.containers.run(
                    image=image,
                    command=args,
                    volumes={
                        AUTOREDUCE_HOME_ROOT: {
                            'bind': '/home/isisautoreduce/.autoreduce/',
                            'mode': 'rw'
                        },
                        ARCHIVE_ROOT: {
                            'bind': '/isis/',
                            'mode': 'rw'
                        },
                        reduced_data: {
                            'bind': '/instrument/',
                            'mode': 'rw'
                        },
                        temp_dir: {
                            'bind': '/output/',
                            'mode': 'rw'
                        },
                    },
                    stdin_open=True,
                    environment=["AUTOREDUCTION_PRODUCTION=1", "PYTHONIOENCODING=utf-8"],
                    stdout=True,
                    stderr=True,
                )

                logger.info("Container logs %s", container.decode("utf-8"))

                with open(f'{temp_dir}/output.txt', encoding="utf-8", mode='r') as out_file:
                    result_message_raw = out_file.read()

                result_message = Message()

                result_message.populate(result_message_raw)

        # If the specified image does not exist.
        except ImageNotFound as exc:
            raise exc
        # If the server returns an error.
        except APIError as exc:
            raise exc
        # If the container exits with a non-zero exit code and detach is False.
        except ContainerError as exc:
            raise exc
        except Exception:  # pylint:disable=broad-except
            logger.error("Processing encountered an error: %s", traceback.format_exc())
            self.message.message = f"Processing encountered an error: {traceback.format_exc()}"
            result_message = self.message

        return result_message
