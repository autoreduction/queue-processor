# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# !/usr/bin/env python
"""
Module to demonise the autoreduction processor.
"""

from queue_processors.daemon import Daemon, control_daemon_from_cli
from queue_processors.autoreduction_processor import autoreduction_processor


class AutoreduceQueueProcessorDaemon(Daemon):  # pragma: no cover
    """ Class responsible for running the autoreduction processor. """
    def run(self):
        """ Run autoreduction_processor. """
        autoreduction_processor.main()
        while True:
            pass


def main():
    """ Main method. """
    daemon = AutoreduceQueueProcessorDaemon('/tmp/AutoreduceQueueProcessorDaemon.pid')
    control_daemon_from_cli(daemon)


if __name__ == "__main__":  # pragma: no cover
    main()
