"""
The Daemon that will run the ArchiveMonitor
"""
import sys
import time
from daemon import Daemon
from EndOfRunMonitor.ISIS_archive_monitor import ArchiveMonitor
from EndOfRunMonitor.database_client import session


class ArchiveMonitorDaemon(Daemon):
    """
    Daemon process to run the ArchiveMonitor
    """
    @staticmethod
    def run():
        monitor = ArchiveMonitor('GEM')
        status = monitor.compare_most_recent_to_reduction_db()


if __name__ == "__main__":
    daemon = ArchiveMonitorDaemon('/tmp/ArchiveMonitorDaemon.pid')
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
