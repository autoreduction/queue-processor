"""
Holds the class for overidding QueueService framework

This is a windows service rather than a daemon due to issues
with correctly watching files through mounting the ISIS archive.
As the ISIS archive would be mounted as a drive, this causes
difficulties whne watching for file changes.
"""
# pylint: disable=import-error
from datetime import datetime
import logging
import os

from monitors.service_helpers import compare_time
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
        last_check = datetime.now()
        while 1:
            # Wait for service stop signal, if I timeout, loop again
            rc = win32event.WaitForSingleObject(self.hWaitStop, self.timeout)
            # Check the health of the system
            if compare_time(datetime.now(), last_check, 10):
                last_check = datetime.now()
                if not health_check():
                    logging.warning('Problem detected. Restarting service...')
                    end_of_run_monitor.stop()
                    end_of_run_monitor.main()
                else:
                    logging.info('No problems detected with service')
            # Check to see if self.hWaitStop happened
            if rc == win32event.WAIT_OBJECT_0:
                # Stop signal encountered
                servicemanager.LogInfoMsg(self._svc_name_ + " - STOPPED")
                end_of_run_monitor.stop()
                break


def health_check():
    """
    Check to see if the service is still running as expected
    :return: True: Service is okay, False: Service requires restart
    """
    logging.info('Performing Health check at %s', datetime.now())
    return True


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
