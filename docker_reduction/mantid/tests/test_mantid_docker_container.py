# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests that the mantid docker container can be built and can run a simple reduction script
"""
import unittest
import os

from mock import patch
import docker

from docker_reduction.mount import Mount
from docker_reduction.mantid.operations import MantidDocker
from docker_reduction.mantid.mounts import DATA_IN, DATA_OUT



class TestMantidDockerContainer(unittest.TestCase):
    """
    Test the Mantid Docker container functionality
    """

    def setUp(self):
        """
        Create a MantidDocker object using the input and output directories in the
        docker_reduction/mantid/tests/ directory
        """
        test_directory = os.path.dirname(os.path.realpath(__file__))
        test_input_directory = os.path.join(test_directory, 'input')
        test_output_directory = os.path.join(test_directory, 'output')
        self.input_mount = self._create_test_input_mount(test_input_directory)
        self.output_mount = self._create_test_output_mount(test_output_directory)
        self.script_location = os.path.join(self.input_mount.container_destination,
                                            'load_script.py')
        self.input_data_location = os.path.join(self.input_mount.container_destination,
                                                'FakeWorkspace.nxs')
        self.mantid_docker = MantidDocker(reduction_script=self.script_location,
                                          input_file=self.input_data_location,
                                          output_directory=self.output_mount.container_destination,
                                          input_mount=self.input_mount,
                                          output_mount=self.output_mount)

    def test_init(self):
        """ Ensure initialisation is successful """
        self.assertEqual(self.mantid_docker.image_name, 'mantid-reduction-container')
        self.assertEqual(self.mantid_docker.reduction_script, self.script_location)
        self.assertEqual(self.mantid_docker.input_file, self.input_data_location)
        self.assertEqual(self.mantid_docker.output_directory,
                         self.output_mount.container_destination)
        self.assertEqual(self.mantid_docker.input_mount, self.input_mount)
        self.assertEqual(self.mantid_docker.output_mount, self.output_mount)

    def test_build(self):
        """ Ensure that the image can be built from the Dockerfile"""
        self.mantid_docker.build()
        client = docker.from_env()
        for image in client.images.list():
            for tag in image.tags:
                if self.mantid_docker.image_name in str(tag):
                    return
        # pragma: no cover
        self.fail('Image name: {} . Not found in image list: {}'
                  .format(self.mantid_docker.image_name, client.images.list()))

    def test_create_volumes_default(self):
        """ Ensure the volumes are created correctly when volumes are specified """
        # Create a dummy MantidDocker object
        default_mantid_docker = MantidDocker(reduction_script='test',
                                             input_file='test',
                                             output_directory='test')
        self.assertEqual(default_mantid_docker.input_mount, None)
        self.assertEqual(default_mantid_docker.output_mount, None)
        actual = default_mantid_docker.create_volumes()
        expected = {DATA_IN.host_location: {'bind': DATA_IN.container_destination, 'mode': 'ro'},
                    DATA_OUT.host_location: {'bind': DATA_OUT.container_destination, 'mode': 'rw'}}
        self.assertEqual(actual, expected)

    def test_create_volumes_non_default(self):
        """ Ensure the volumes are created correctly when volumes are NOT specified """
        self.assertEqual(self.mantid_docker.input_mount, self.input_mount)
        self.assertEqual(self.mantid_docker.output_mount, self.output_mount)
        actual = self.mantid_docker.create_volumes()
        # pylint:disable=line-too-long
        expected = {self.input_mount.host_location: {'bind': self.input_mount.container_destination, 'mode': 'ro'},
                    self.output_mount.host_location: {'bind': self.output_mount.container_destination, 'mode': 'rw'}}
        self.assertEqual(actual, expected)

    def test_create_environment_variables(self):
        """ Ensure the environmental variables are created correctly """
        actual = self.mantid_docker.create_environment_variables()
        expected = {'SCRIPT': self.script_location,
                    'INPUT_FILE': self.input_data_location,
                    'OUTPUT_DIR': self.output_mount.container_destination}
        self.assertEqual(actual, expected)

    def test_reduce_simple(self):
        """
        Test if the container can successfully run the script in
        docker_reduction/mantid/tests/input/load_script.py
        """
        self.mantid_docker.run(self.mantid_docker.create_volumes(),
                               self.mantid_docker.create_environment_variables())
        self.assertTrue(os.path.isfile(os.path.join(self.output_mount.host_location,
                                                    'load-successful.nxs')))
        self._clean_output_directory()

    @patch('docker_reduction.mantid.operations.MantidDocker.build')
    @patch('docker_reduction.mantid.operations.MantidDocker.create_volumes')
    @patch('docker_reduction.mantid.operations.MantidDocker.create_environment_variables')
    @patch('docker_reduction.mantid.operations.MantidDocker.run')
    def test_perform_reduction(self, mock_run, mock_env_var, mock_vol, mock_build):
        """ Ensure all reduction steps are performed in workflow function """
        self.mantid_docker.perform_reduction()
        mock_build.assert_called_once()
        mock_vol.assert_called_once()
        mock_env_var.assert_called_once()
        mock_run.assert_called_once()

    def _clean_output_directory(self):
        """
        Remove the files in the output directory
        """
        folder = self.output_mount.host_location
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except OSError:
                pass  # this only happens when the function is called but nothing is there!

    @staticmethod
    def _create_test_input_mount(input_directory):
        """
        :return: Custom Mount object that points to the test input directory
        """
        return Mount(host_location=input_directory,
                     container_destination='/isis/')

    @staticmethod
    def _create_test_output_mount(output_directory):
        """
        :return: Custom Mount object that points to the test output directory
        """
        return Mount(host_location=output_directory,
                     container_destination='/instrument/')
