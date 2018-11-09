"""
Holds the class for overidding QueueService framework

This is a windows service rather than a daemon due to issues
with correctly watching files through mounting the ISIS archive.
As the ISIS archive would be mounted as a drive, this causes
difficulties whne watching for file changes.
"""
# Required for linux pylint build not to fail
# pylint: disable=import-error
import os

#from monitors.health_check import HealthCheckThread
from monitors import end_of_run_monitor

if os.name == "nt":

    import servicemanager
    import win32api
    import win32event
    import win32service
    import win32serviceutil


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

        end_of_run_monitor.main()
        #health_check_thread = HealthCheckThread(600)  # 10 minutes
        #health_check_thread.start()
        while 1:
            # Wait for service stop signal, if I timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            # Check to see if self.hWaitStop happened
            if rc == win32event.WAIT_OBJECT_0:
                # Stop signal encountered
                servicemanager.LogInfoMsg(self._svc_name_ + " - STOPPED")
                end_of_run_monitor.stop()
                #health_check_thread.stop()
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
