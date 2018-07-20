"""
Holds the class for overidding QueueService framework
"""
# Can't import on travis (linux) server
# pylint:disable=import-error
import sys
import servicemanager
import win32event
import win32serviceutil

from monitors.windows_service import WindowsService
from monitors.archive_monitor import isis_archive_monitor


class PollService(WindowsService):
    """
    Class to override windows ServiceFramework
    """
    _svc_name_ = "AutoReductionArchiveMonitor"
    _svc_display_name_ = "Autoreduce Archive Monitor"
    _svc_description_ = "Polls ISIS data archive directory to check for new files"

    # pylint: disable=invalid-name
    def SvcDoRun(self):
        """
        Run the main function in isis_archive_monitor which starts the polling process
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


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PollService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PollService)
