#!/usr/bin/env python
"""
Module for daemonising the queue processor.
"""
import sys
from daemon import Daemon
import queue_processor


class QueueProcessorDaemon(Daemon):
    """ Queue processor daemoniser """
    def run(self):
        """ Run queue processor. """
        queue_processor.main()
        while True:
            pass


def main():
    """ Main method. """
    daemon = QueueProcessorDaemon('/tmp/QueueProcessorDaemon.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
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
