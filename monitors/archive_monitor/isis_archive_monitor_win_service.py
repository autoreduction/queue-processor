"""
Holds the class for overidding QueueService framework
"""
# Can't import on travis (linux) server
# pylint:disable=import-error
import sys
import time

import servicemanager
import win32event
import win32serviceutil

from monitors.windows_service import WindowsService
from monitors.archive_monitor.isis_archive_monitor import ArchiveMonitor
from monitors.archive_monitor.isis_archive_monitor_helper import SLEEP_TIME


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
        monitor = ArchiveMonitor("POLARIS")
        while 1:
            monitor.perform_check()
            if monitor.restart_end_of_run_monitor:
                self.restart_end_of_run_monitor()
            sleep_timer = 0
            end_service_loop = False
            while sleep_timer < SLEEP_TIME:
                time_to_sleep = 30 if SLEEP_TIME > 30 else SLEEP_TIME
                time.sleep(time_to_sleep)
                # Wait for service stop signal, if I timeout, loop again
                rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
                # Check to see if self.hWaitStop happened
                if rc == win32event.WAIT_OBJECT_0:
                    # Stop signal encountered
                    servicemanager.LogInfoMsg(self._svc_name_ + " - STOPPED")
                    end_service_loop = True
                    break
                sleep_timer += time_to_sleep
            if end_service_loop:
                break

    @staticmethod
    def restart_end_of_run_monitor():
        """
        Restart the end of run monitor windows service
        """
        win32serviceutil.RestartService("AutoreduceInstrumentMonitor")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PollService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PollService)
