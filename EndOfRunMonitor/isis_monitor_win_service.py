"""
Holds the class for overidding QueueService framework

This is a windows service rather than a daemon due to issues
with correctly watching files through mounting the ISIS archive.
As the ISIS archive would be mounted as a drive, this causes
difficulties whne watching for file changes.
"""
# ToDo: check if unused-import warning is legitimate for win32con, win32evtlogutil
# pylint: disable=import-error, unused-import
import os

if os.system == "nt":

    import servicemanager
    import win32api
    import win32con
    import win32event
    import win32evtlogutil
    import win32service
    import win32serviceutil

from EndOfRunMonitor import ISISendOfRunMonitor


class QueueService(win32serviceutil.ServiceFramework):
    """
    Class to override windows ServiceFramework
    """
    _svc_name_ = "AutoreduceInstrumentMonitor"
    _svc_display_name_ = "Autoreduce Instrument Monitor"
    _svc_description_ = ""
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

        ISISendOfRunMonitor.main()
        while 1:
            # Wait for service stop signal, if I timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            # Check to see if self.hWaitStop happened
            if rc == win32event.WAIT_OBJECT_0:
                # Stop signal encountered
                servicemanager.LogInfoMsg(self._svc_name_ + " - STOPPED")
                ISISendOfRunMonitor.stop()
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
