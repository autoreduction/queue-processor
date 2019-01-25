# !/usr/bin/env python
"""
Module to demonise the autoreduction processor.
"""
import sys
from QueueProcessors.AutoreductionProcessor.daemon import Daemon
from QueueProcessors.AutoreductionProcessor import autoreduction_processor


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


if __name__ == "__main__":  # pragma: no cover
    main()
