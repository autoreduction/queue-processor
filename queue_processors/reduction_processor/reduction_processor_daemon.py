# !/usr/bin/env python
"""
Module to demonise the autoreduction processor.
"""
import sys

from queue_processors.daemon import Daemon
from queue_processors.reduction_processor import reduction_processor


class AutoreduceQueueProcessorDaemon(Daemon):
    """ Class responsible for running the autoreduction processor. """
    def run(self):
        """ Run autoreduction_processor. """
        reduction_processor.main()
        while True:
            pass


def main():
    """ Main method. """
    daemon = AutoreduceQueueProcessorDaemon('/tmp/reduction_processor_daemon.pid')
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            daemon.start()
        elif sys.argv[1] == 'stop':
            daemon.stop()
        elif sys.argv[1] == 'restart':
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)


if __name__ == "__main__":
    main()
