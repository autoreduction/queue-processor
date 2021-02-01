# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

# !/usr/bin/env python
"""
Module for daemonising the queue processor.
"""
import logging
import signal
import time
from typing import Optional
from utils.clients.queue_client import QueueClient

from queue_processors.daemon import Daemon, control_daemon_from_cli
from queue_processors.queue_processor import queue_listener


class QueueListenerDaemon(Daemon):
    """ Queue Listener daemoniser """
    def __init__(self, *args, **kwargs):
        """ Initialise the queue_processor daemon """
        super().__init__(*args, **kwargs)

        self.client: Optional[QueueClient] = None
        self.listener: Optional[queue_listener.QueueListener] = None
        self.logger = logging.getLogger(__file__)
        self._shutting_down = False

        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

    def run(self):
        """ Run queue processor. """
        self.logger.info("Starting Queue Processor")
        self.client, self.listener = queue_listener.main()
        # keeps the daemon alive as the main call above does not block
        # but simply runs the connections in async. If this sleep isn't
        # here the deamon will just exit after connecting
        while not self._shutting_down:
            time.sleep(0.5)

    def stop(self, *_):
        """
        Stops the Queue Processor Daemon, first making sure that
        the underlying client has finished
        """
        if self.client is None or self.listener is None:
            raise RuntimeError("The QueueListenerDaemon was never started!")

        if self.listener.is_processing_message():
            self.logger.info("Shutdown requested but the listener is processing a run. "
                             "The client will wait for it to finish before exiting.")
        self.client.disconnect()
        self._shutting_down = True
        self.logger.info("Queue Processor exited gracefully from SIGTERM")


def main():
    """ Main method. """
    daemon = QueueListenerDaemon('/tmp/QueueListenerDaemon.pid')
    control_daemon_from_cli(daemon)


if __name__ == "__main__":
    main()
