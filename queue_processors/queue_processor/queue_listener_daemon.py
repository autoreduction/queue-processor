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

from queue_processors.daemon import Daemon, control_daemon_from_cli
from queue_processors.queue_processor import queue_listener
from queue_processors.queue_processor.settings import LOGGING

logging.config.dictConfig(LOGGING)


class QueueListenerDaemon(Daemon):
    """ Queue Listener daemoniser """
    def __init__(self, *args, **kwargs):
        """
        Sets the time to shutdown and a handler for the Daemon
        This time was selected so that the cron job will restart roughly
        at the same time each day whilst accounting for thread timing drift.

        If it was set to dead 24 hours we might stop after
        cron tries to start us. So we take a 15 minute time buffer where
        the QP is offline to give us a window where we can shutdown.
        """
        super().__init__(*args, **kwargs)

        self._client_handle = None
        self._logger = logging.getLogger(__file__)
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

    def run(self):
        """ Run queue processor. """
        self._logger.info("Starting Queue Processor")
        self._client_handle = queue_listener.main()
        # keeps the daemon alive as the main call above does not block
        # but simply runs the connections in async. If this sleep isn't
        # here the deamon will just exit after connecting
        while True:
            time.sleep(0.5)

    def stop(self):
        """
        Stops the Queue Processor Daemon, first making sure that
        the underlying client has finished
        """
        if self._client_handle is None:
            print("Cannot safely disconnect _client_handle as it is "
                  "running in original process. Messages might get lost. "
                  "This happens when the process is manually stopped from CLI.")
        else:
            self._client_handle.disconnect()
        super().stop()
        self._logger.info("Queue Processor exited gracefully from SIGTERM")


def main():
    """ Main method. """
    daemon = QueueListenerDaemon('/tmp/QueueListenerDaemon.pid')
    control_daemon_from_cli(daemon)


if __name__ == "__main__":
    main()
