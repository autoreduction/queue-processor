"""
All docker operations for running reduced data
"""
import os

import docker
from docker_containers.mantid.docker_settings import (DATA_IN, DATA_OUT)


IMAGE_NAME = 'reduction-container'


def build():
    """
    Build the Mantid docker container
    Note that the Mantid.user.properties file MUST be in the same directory as this file
    """
    client = docker.from_env()
    client.images.build(path=os.path.dirname(os.path.realpath(__file__)),
                        tag=IMAGE_NAME)


def run(script, input_file, output_directory, data_in_mount=None, data_out_mount=None):
    """
    Run the reduction script from the ISIS data archive through Mantid
    If data_in/out_mount are not defined then attempt to use the default
    :param script: Full path to the reduction script
    :param input_file: The .nxs file that should be reduced
    :param output_directory: The directory that the results should be saved to
    :param data_in_mount: Optional mount to input data directory
    :param data_out_mount: Optional mount to output data directory
    """
    # Use defaults for mount directories if not supplied
    data_in = data_in_mount if data_in_mount else DATA_IN
    data_out = data_out_mount if data_out_mount else DATA_OUT

    client = docker.from_env()
    # Volumes
    volumes = {data_in.host_location: {'bind': data_in.container_destination, 'mode': 'ro'},
               data_out.host_location: {'bind': data_out.container_destination, 'mode': 'rw'}}
    # Environment variables
    environment = {'SCRIPT': script,
                   'INPUT_FILE': input_file,
                   'OUTPUT_DIR': output_directory}
    # Run the container
    client.containers.run(image=IMAGE_NAME,
                          volumes=volumes,
                          environment=environment)
