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
import threading
import logging
import datetime

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

        # For more details on why this daemon shuts itself down on a timer
        # check the README.md in this directory!
        stop_hours = 23
        stop_minutes = 45
        # ((hours -> Mins) + Mins) -> seconds)  => Stored in seconds
        self.safe_shutdown = threading.Event()
        self.stop_interval = ((stop_hours * 60) + stop_minutes) * 60

        self._client_handle = None
        self._stop_timer = None
        self._logger = logging.getLogger(__file__)

    def run(self):
        """ Run queue processor. """
        self._logger.info("Starting Queue Processor")
        self._client_handle = queue_listener.main()
        self._logger.info("Setting shutdown timer for %s", str(datetime.datetime.now()+datetime.timedelta(hours=23, minutes=45)))
        self._stop_timer = threading.Timer(self.stop_interval, self.stop)
        self._stop_timer.start()

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
            self.safe_shutdown.set()
        super().stop()



def _wait_for_client(daemon):
    # Give 1 minute (60 s) to shutdown once stop has been called
    was_safe_shutdown = daemon.safe_shutdown.wait(timeout=60)

    if not was_safe_shutdown:
        log = logging.getLogger(__file__)
        # You will also see this message in the log if manually stop the process
        # that is expected and is OK. If seen and not manually shut-down
        # this means the client_handle did not disconnect in time and was
        # in the middle of processing something!
        log.error("%s: Queue Client did not shutdown gracefully before timeout, "
                  "so it was killed. This should be investigated as it could "
                  "cause messages to get lost.", datetime.datetime.now().isoformat())


def main():
    """ Main method. """
    daemon = QueueListenerDaemon('/tmp/QueueListenerDaemon.pid')
    control_daemon_from_cli(daemon, _wait_for_client)


if __name__ == "__main__":
    main()
