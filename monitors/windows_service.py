"""
Holds the class for overidding QueueService framework

This is a windows service rather than a daemon due to issues
with correctly watching files through mounting the ISIS archive.
As the ISIS archive would be mounted as a drive, this causes
difficulties whne watching for file changes.
"""
# Can't import on travis (linux) server
# pylint:disable=import-error
import win32api
import win32event
import win32service
import win32serviceutil


class WindowsService(win32serviceutil.ServiceFramework):
    """
    Class to override windows ServiceFramework
    """
    _svc_name_ = ""
    _svc_display_name_ = ""
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
        This function should always be overridden by the child class
        """
        raise NotImplementedError("This method should always be overridden by the child class")


# pylint: disable=invalid-name
def ctrl_handler(_):
    """
    Expect anonymous input and returns true
    :return: True
    """
    return True


if __name__ == '__main__':
    win32api.SetConsoleCtrlHandler(ctrl_handler, True)
    win32serviceutil.HandleCommandLine(WindowsService)
