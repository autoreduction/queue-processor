"""
Holds the class for overidding QueueService framework
"""
# pylint: disable=import-error
import servicemanager
import win32api
import win32event
import win32service
import win32serviceutil

from EndOfRunMonitor.archive_monitor import isis_archive_monitor


class QueueService(win32serviceutil.ServiceFramework):
    """
    Class to override windows ServiceFramework
    """
    _svc_name_ = "AutoReductionArchiveMonitor"
    _svc_display_name_ = "Autoreduce Archive Monitor"
    _svc_description_ = "Polls ISIS data archive directory to check for new files"
    timeout = 3000

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        # pylint: disable=invalid-name
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    # pylint: disable=invalid-name
    def SvcStop(self):
        """
        Stop the service running
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    # pylint: disable=invalid-name
    def SvcDoRun(self):
        """
        Perform a run
        """
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))

        isis_archive_monitor.main()
        while 1:
            # Wait for service stop signal, if I timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            # Check to see if self.hWaitStop happened
            if rc == win32event.WAIT_OBJECT_0:
                # Stop signal encountered
                servicemanager.LogInfoMsg(self._svc_name_ + " - STOPPED")
                break


# pylint: disable=invalid-name
def ctrl_handler(_):
    """
    Expect anonymous input and returns true
    :return: True
    """
    return True


if __name__ == '__main__':
    win32api.SetConsoleCtrlHandler(ctrl_handler, True)
    win32serviceutil.HandleCommandLine(QueueService)
