"""
module to run daemon process for ISIS monitor
"""
import sys

# pylint: disable=no-name-in-module
from daemon import Daemon
from EndOfRunMonitor import ISISendOfRunMonitor


# pylint: disable=too-few-public-methods
class InstrumentMonitorDaemon(Daemon):
    """
    class to abstract from __main__
    """
    @staticmethod
    def run():
        """
        class function to run __main__
        """
        ISISendOfRunMonitor.main()


if __name__ == "__main__":
    DAEMON = InstrumentMonitorDaemon('/tmp/InstrumentMonitorDaemon.pid')
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            DAEMON.start()
        elif sys.argv[1] == 'stop':
            DAEMON.stop()
        elif sys.argv[1] == 'restart':
            DAEMON.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
