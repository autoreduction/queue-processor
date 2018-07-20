"""
Holds the class for overidding QueueService framework

This is a windows service rather than a daemon due to issues
with correctly watching files through mounting the ISIS archive.
As the ISIS archive would be mounted as a drive, this causes
difficulties whne watching for file changes.
"""
# Can't import on travis (linux) server
# pylint:disable=import-error
import sys
import servicemanager
import win32event
import win32serviceutil

from monitors.end_of_run_monitor import isis_end_of_run_monitor
from monitors.windows_service import WindowsService


class MonitorService(WindowsService):
    """
    Class to override windows ServiceFramework
    """
    _svc_name_ = "AutoreduceInstrumentMonitor"
    _svc_display_name_ = "Autoreduce Instrument Monitor"
    _svc_description_ = "Listens for updates on the lastrun.txt file in the ISIS archive"

    # pylint: disable=invalid-name
    def SvcDoRun(self):
        """
        Run the main function in isis_end_of_run_monitor which starts the watchdog observer
        """
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))

        isis_end_of_run_monitor.main()
        while 1:
            # Wait for service stop signal, if I timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            # Check to see if self.hWaitStop happened
            if rc == win32event.WAIT_OBJECT_0:
                # Stop signal encountered
                servicemanager.LogInfoMsg(self._svc_name_ + " - STOPPED")
                isis_end_of_run_monitor.stop()
                break


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MonitorService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MonitorService)
