# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Linux only!
Tests that data can traverse through the autoreduction system successfully
"""
import subprocess
import time

from autoreduce_utils.clients import queue_client
from autoreduce_utils.clients.settings.client_settings_factory import ClientSettingsFactory

from autoreduce_qp.systemtests.base_systemtest import BaseAutoreduceSystemTest, REDUCE_SCRIPT


class TestActiveMQReconnect(BaseAutoreduceSystemTest):
    """Tests that the Queue Listener reconnects after ActiveMQ goes down"""
    @classmethod
    def setUpClass(cls):
        """ Start all external services """
        settings_factory = ClientSettingsFactory()
        cls.original_activemq_credentials = queue_client.ACTIVEMQ_CREDENTIALS

        queue_client.ACTIVEMQ_CREDENTIALS = settings_factory.create('queue',
                                                                    username="admin",
                                                                    password="admin",
                                                                    host="127.0.0.1",
                                                                    port="62000")
        cls._start_activemq()

    @classmethod
    def tearDownClass(cls):
        cls._stop_activemq()
        queue_client.ACTIVEMQ_CREDENTIALS = cls.original_activemq_credentials

    @staticmethod
    def _start_activemq():
        subprocess.run("docker run --rm --name activemq_systemtest -p 62000:61613 -d rmohr/activemq",
                       shell=True,
                       timeout=30,
                       check=True)
        time.sleep(30)

    @staticmethod
    def _stop_activemq():
        subprocess.run("docker kill activemq_systemtest", shell=True, timeout=30, check=True)

    def test_reconnect_on_activemq_failure(self):
        """
        Test: Listener is still listening
        When: ActiveMQ has started after stopping
        """
        self._stop_activemq()
        self._start_activemq()

        file_location = self._setup_data_structures(reduce_script=REDUCE_SCRIPT, vars_script='')
        self.data_ready_message.data = file_location

        results = self.send_and_wait_for_result(self.data_ready_message)

        assert results is not None
        assert len(results) == 1
