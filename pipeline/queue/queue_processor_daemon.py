# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
#!/usr/bin/env python
"""
Module for daemonising the queue processor.
"""
from pipeline.daemon import Daemon, control_daemon_from_cli
from pipeline.queue import stomp_client


class QueueProcessorDaemon(Daemon):
    """ Queue processor daemoniser """
    def run(self):
        """ Run queue processor. """
        stomp_client.main()
        while True:
            pass


def main():
    """ Main method. """
    daemon = QueueProcessorDaemon('/tmp/QueueProcessorDaemon.pid')
    control_daemon_from_cli(daemon)


if __name__ == "__main__":
    main()
