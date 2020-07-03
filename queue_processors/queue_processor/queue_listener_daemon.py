# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

# !/usr/bin/env python
"""
Module for daemonising the queue processor.
"""
import threading
import logging
from queue_processors.daemon import Daemon, control_daemon_from_cli
from queue_processors.queue_processor import queue_listener


class QueueListenerDaemon(Daemon):
    """ Queue Listener daemoniser """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This time was selected so that the cron job will restart roughly
        # at the same time each day whilst accounting for thread timing drift.

        # If it was set to dead 24 hours we might end up stopping after
        # cron tries to start us. So we take a 15 minute time buffer where
        # the QP is offline to give us a window where we can shutdown.
        stop_hours = 23
        stop_minutes = 45
        # ((hours -> Mins) + Mins) -> seconds)  => Stored in seconds
        self.safe_shutdown = threading.Event()
        self.stop_interval = ((stop_hours * 60) + stop_minutes) * 60

        self._client_handle = None
        self._stop_timer = None

    def run(self):
        """ Run queue processor. """
        self._client_handle = queue_listener.main()
        self._stop_timer = threading.Timer(self.stop_interval, self.stop)
        self._stop_timer.start()

    def stop(self):
        """
        Stops the Queue Processor Daemon, first making sure that
        the underlying client has finished
        """
        self._client_handle.disconnect()
        super().stop()
        self.safe_shutdown.set()


def _wait_for_client(daemon):
    # Give 1 minute (60 s) to shutdown once stop has been called
    timeout = 60 + daemon.stop_interval
    was_safe_shutdown = daemon.safe_shutdown.wait(timeout=timeout)

    if not was_safe_shutdown:
        logging.error(
            "Queue Client did not shutdown before timeout, so it was killed"
            " ungracefully. This should be investigated as it could cause"
            " messages to get lost.")


def main():
    """ Main method. """
    daemon = QueueListenerDaemon('/tmp/QueueListenerDaemon.pid')
    control_daemon_from_cli(daemon)
    _wait_for_client(daemon)


if __name__ == "__main__":
    main()
