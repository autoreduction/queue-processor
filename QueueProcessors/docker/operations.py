"""
All docker operations for running reduced data
"""
import os

import docker
from QueueProcessors.docker.docker_settings import (REDUCTION_SCRIPT_DIRECTORY,
                                                    CALIBRATION_DIRECTORY,
                                                    OUTPUT_DIRECTORY)


IMAGE_NAME = 'reduction-container'


def build():
    client = docker.from_env()
    client.images.build(path=os.path.dirname(os.path.realpath(__file__)),
                        tag=IMAGE_NAME)


def run():
    client = docker.from_env()
    volumes = {REDUCTION_SCRIPT_DIRECTORY, {'bind': '/mount/script', 'mode': 'r'},
               OUTPUT_DIRECTORY, {'bind': '/mount/output', 'mode': 'rw'}}
    if CALIBRATION_DIRECTORY:
        volumes[CALIBRATION_DIRECTORY] = {'bind': '/mount/calibration', 'mode': 'r'}
    client.containers.run(image=IMAGE_NAME,
                          volumes=volumes)
