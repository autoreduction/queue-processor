# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests that the mantid docker container can be built and can run a simple reduction script
"""
import unittest
import os

from unittest.mock import patch, MagicMock

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
        self.script_location = os.path.join(self.input_mount.container_destination, 'load_script.py')
        self.input_data_location = os.path.join(self.input_mount.container_destination, 'FakeWorkspace.nxs')
        self.mantid_docker = MantidDocker(reduction_script=self.script_location,
                                          input_file=self.input_data_location,
                                          output_directory=self.output_mount.container_destination,
                                          input_mount=self.input_mount,
                                          output_mount=self.output_mount)

    def test_init(self):
        """
        Test: All the expected member variables are created
        When: The class is initialised
        """
        self.assertEqual(self.mantid_docker.image_name, 'mantid-reduction-container')
        self.assertEqual(self.mantid_docker.reduction_script, self.script_location)
        self.assertEqual(self.mantid_docker.input_file, self.input_data_location)
        self.assertEqual(self.mantid_docker.output_directory, self.output_mount.container_destination)
        self.assertEqual(self.mantid_docker.input_mount, self.input_mount)
        self.assertEqual(self.mantid_docker.output_mount, self.output_mount)

    @patch("docker.from_env")
    @patch("os.path.realpath")
    @patch("os.path.dirname", return_value="valid_build_path")
    @patch("os.path.join", return_value="valid_dockerfile")
    def test_build(self, mock_join, mock_dirname, mock_realpath, mock_from_env):
        """
         Test: DockerClient.images.build is called with the correct kwargs
         When: MantidDocker.build is called
         """
        mock_docker_client = MagicMock()
        mock_from_env.return_value = mock_docker_client
        self.mantid_docker.build()

        mock_from_env.assert_called_once()
        mock_realpath.assert_called_once()
        mock_dirname.assert_called_once()
        mock_join.assert_called_once()
        mock_docker_client.images.build.assert_called_once()

        (_, kwargs) = mock_docker_client.images.build.call_args
        self.assertEqual(list(kwargs.keys()), ["path", "dockerfile", "tag"])
        self.assertEqual(kwargs["path"], "valid_build_path")
        self.assertEqual(kwargs["dockerfile"], "valid_dockerfile")
        self.assertEqual(kwargs["tag"], self.mantid_docker.image_name)

    def test_create_volumes_default(self):
        """
        Test: The volumes are created correctly
        When: MantidDocker.create_volumes is called and volumes are specified
        """
        # Create a dummy MantidDocker object
        default_mantid_docker = MantidDocker(reduction_script='test', input_file='test', output_directory='test')
        self.assertEqual(default_mantid_docker.input_mount, None)
        self.assertEqual(default_mantid_docker.output_mount, None)
        actual = default_mantid_docker.create_volumes()
        expected = {
            DATA_IN.host_location: {
                'bind': DATA_IN.container_destination,
                'mode': 'ro'
            },
            DATA_OUT.host_location: {
                'bind': DATA_OUT.container_destination,
                'mode': 'rw'
            }
        }
        self.assertEqual(actual, expected)

    def test_create_volumes_non_default(self):
        """
        Test: The volumes are created correctly
        When: MantidDocker.create_volumes is called and volumes are NOT specified
        """
        self.assertEqual(self.mantid_docker.input_mount, self.input_mount)
        self.assertEqual(self.mantid_docker.output_mount, self.output_mount)
        actual = self.mantid_docker.create_volumes()
        # pylint:disable=line-too-long
        expected = {
            self.input_mount.host_location: {
                'bind': self.input_mount.container_destination,
                'mode': 'ro'
            },
            self.output_mount.host_location: {
                'bind': self.output_mount.container_destination,
                'mode': 'rw'
            }
        }
        self.assertEqual(actual, expected)

    def test_create_environment_variables(self):
        """
        Test: The environmental variables are created correctly
        When: MantidDocker.create_environment_variables is called
        """
        actual = self.mantid_docker.create_environment_variables()
        expected = {
            'SCRIPT': self.script_location,
            'INPUT_FILE': self.input_data_location,
            'OUTPUT_DIR': self.output_mount.container_destination
        }
        self.assertEqual(actual, expected)

    @patch("docker.from_env")
    def test_reduce_simple(self, mock_from_env):
        """
        Test: DockerClient.containers.run is called with the correct kwargs
        When: MantidDocker.run is called with given arguments
        """
        mock_docker_client = MagicMock()
        mock_from_env.return_value = mock_docker_client
        self.mantid_docker.run("volumes", "environment_variables")

        mock_from_env.assert_called_once()
        mock_docker_client.containers.run.assert_called_once()

        (_, kwargs) = mock_docker_client.containers.run.call_args
        self.assertEqual(list(kwargs.keys()), ["image", "volumes", "environment"])
        self.assertEqual(kwargs["image"], self.mantid_docker.image_name)
        self.assertEqual(kwargs["volumes"], "volumes")
        self.assertEqual(kwargs["environment"], "environment_variables")

    @patch('docker_reduction.mantid.operations.MantidDocker.build')
    @patch('docker_reduction.mantid.operations.MantidDocker.create_volumes')
    @patch('docker_reduction.mantid.operations.MantidDocker.create_environment_variables')
    @patch('docker_reduction.mantid.operations.MantidDocker.run')
    def test_perform_reduction(self, mock_run, mock_env_var, mock_vol, mock_build):
        """
        Test: All reduction steps are performed in workflow function
        When: MantidDocker.perform_reduction is called
        """
        self.mantid_docker.perform_reduction()
        mock_build.assert_called_once()
        mock_vol.assert_called_once()
        mock_env_var.assert_called_once()
        mock_run.assert_called_once()

    @staticmethod
    def _create_test_input_mount(input_directory):
        """
        :return: Custom Mount object that points to the test input directory
        """
        return Mount(host_location=input_directory, container_destination='/isis/')

    @staticmethod
    def _create_test_output_mount(output_directory):
        """
        :return: Custom Mount object that points to the test output directory
        """
        return Mount(host_location=output_directory, container_destination='/instrument/')
