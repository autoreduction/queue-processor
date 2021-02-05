# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
All docker operations for running reduced data
"""
import os

import docker
from docker_reduction.mantid.mounts import (DATA_IN, DATA_OUT)


class MantidDocker:
    """
    Class that contains the information required to perform
    a data reduction inside the mantid docker container
    """

    # pylint:disable=too-many-arguments
    def __init__(self, reduction_script, input_file, output_directory, input_mount=None, output_mount=None):
        self.image_name = 'mantid-reduction-container'
        self.reduction_script = reduction_script
        self.input_file = input_file
        self.output_directory = output_directory
        self.input_mount = input_mount
        self.output_mount = output_mount

    def perform_reduction(self):
        """
        Perform a reduction of data inside a mantid docker container
        """
        self.build()
        volumes = self.create_volumes()
        environment_variables = self.create_environment_variables()
        self.run(volumes, environment_variables)

    def build(self):
        """
        Build the Mantid docker container
        Note that the Mantid.user.properties file MUST be in the same directory as this file
        """
        client = docker.from_env()
        build_path = os.path.dirname(os.path.realpath(__file__))
        client.images.build(path=build_path, dockerfile=os.path.join(build_path, 'Dockerfile'), tag=self.image_name)

    def create_volumes(self):
        """
        Construct the volumes expected for mantid
        :return: a dictionary of volumes in the expected format for docker
        """
        # Use defaults for mount directories if not supplied
        data_in = self.input_mount if self.input_mount else DATA_IN
        data_out = self.output_mount if self.output_mount else DATA_OUT
        self.input_mount = data_in
        self.output_mount = data_out

        # Volumes
        volumes = {
            data_in.host_location: {
                'bind': data_in.container_destination,
                'mode': 'ro'
            },
            data_out.host_location: {
                'bind': data_out.container_destination,
                'mode': 'rw'
            }
        }

        return volumes

    def create_environment_variables(self):
        """
        Construct the environment variables required for Mantid reduction
        :return: a dictionary of environment variables in the expected format for docker
        """
        # Environment variables
        environment = {
            'SCRIPT': self.reduction_script,
            'INPUT_FILE': self.input_file,
            'OUTPUT_DIR': self.output_mount.container_destination
        }
        return environment

    def run(self, volumes, environment_variables):
        """
        Run the reduction script from the ISIS data archive through Mantid
        :param volumes: Volumes to mount to the container
        :param environment_variables: Environment variables to use
        """
        client = docker.from_env()
        # Run the container
        client.containers.run(image=self.image_name, volumes=volumes, environment=environment_variables)
