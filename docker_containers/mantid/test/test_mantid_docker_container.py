"""
Tests that the mantid docker container can be built and can run a simple reduction script
"""
import unittest
import os

import docker

from docker_containers.mantid.operations import build, run, IMAGE_NAME
from docker_containers.mantid.docker_settings import Mount


class TestMantidDockerContainer(unittest.TestCase):

    def test_build_container(self):
        build()
        client = docker.from_env()
        images = client.build.list()
        self.assertTrue(IMAGE_NAME in images)

    def test_reduce_simple(self):
        test_directory = os.path.dirname(os.path.realpath(__file__))
        input_directory = os.path.join(test_directory, 'input')
        output_directory = os.path.join(test_directory, 'output')
        # Construct custom mounts for data in/out
        in_mount = Mount(host_location=input_directory,
                         container_destination='/isis/')
        out_mount = Mount(host_location=output_directory,
                          container_destination='/instrument/')
        # Run container
        # ToDo: Need to delete contents of output directory before running
        build()
        run(script=os.path.join(input_directory, 'simple_script.py'),
            # We are not reducing data in the test script, so this name is arbitrary
            input_file='InputFileName',
            output_directory=output_directory,
            data_in_mount=in_mount,
            data_out_mount=out_mount)
        self.assertTrue(os.path.isfile(os.path.join(output_directory, 'InputFileName.nxs')))
