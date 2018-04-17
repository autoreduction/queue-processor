"""
The Daemon that will run the ArchiveMonitor
"""
import sys

# pylint: disable=no-name-in-module
from daemon import Daemon

from EndOfRunMonitor.isis_archive_monitor import ArchiveMonitor


# pylint: disable=too-few-public-methods
class ArchiveMonitorDaemon(Daemon):
    """
    Daemon process to run the ArchiveMonitor
    """
    @staticmethod
    def run():
        """Run the ArchiveMonitor process"""
        monitor = ArchiveMonitor('GEM')
        status = monitor.compare_archive_to_database()


if __name__ == "__main__":
    DAEMON = ArchiveMonitorDaemon('/tmp/ArchiveMonitorDaemon.pid')
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
