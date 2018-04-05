# !/usr/bin/env python
"""
Module to demonise the autoreduction processor.
"""
import sys
from daemon import Daemon
import autoreduction_processor


class AutoreduceQueueProcessorDaemon(Daemon):
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
