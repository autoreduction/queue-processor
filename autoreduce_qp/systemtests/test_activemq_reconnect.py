# ############################################################################### #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Linux only!
Tests that data can traverse through the autoreduction system successfully
"""
import time
import docker

from autoreduce_qp.systemtests.base_systemtest import BaseAutoreduceSystemTest, REDUCE_SCRIPT


class TestActiveMQReconnect(BaseAutoreduceSystemTest):
    """Tests that the Queue Listener reconnects after ActiveMQ goes down"""

    @classmethod
    def setUpClass(cls):
        """ Start all external services """
        cls._start_activemq()

    @classmethod
    def tearDownClass(cls):
        cls._stop_activemq()

    @staticmethod
    def _start_activemq():
        """Start ActiveMQ"""
        docker.from_env(timeout=30).containers.run(name="activemq_systemtest",
                                                   image="rmohr/activemq",
                                                   ports={"61613": "62000"},
                                                   detach=True,
                                                   tty=True,
                                                   auto_remove=True)
        time.sleep(30)

    @staticmethod
    def _stop_activemq():
        """Stop ActiveMQ"""
        container = docker.from_env().containers.get("activemq_systemtest")
        container.kill()

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
