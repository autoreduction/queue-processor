import os
import sys
import time
import smtplib

# The hosts to keep tabs on
monitored_hosts = ["reduce.isis.cclrc.ac.uk"]

# Settings for the email notification
email_host = 'exchsmtp.stfc.ac.uk'
email_port = 25
email_recipients = ['isisreduce@stfc.ac.uk']
email_sender = 'monitor@autoreduce.isis.cclrc.ac.uk'
this_host = 'autoreduce.isis.cclrc.ac.uk'


class Monitor(object):
    def __init__(self, hostname_list=monitored_hosts):
        """
        hostnameList should be a list of hostname strings;
        hostList will be a zip of these names and whether they passed their last ping test.
        """
        self.hostList = [(hostname, True) for hostname in hostname_list]

    def loop(self):
        """
        Check all hosts once every minute and update their statuses.
        """
        while True:
            self.hostList = [self.check(*tup) for tup in self.hostList]
            time.sleep(60)

    def check(self, hostname, was_up):
        """ Ping the given host, and if its status has changed, send a notification; returns its new state. """
        is_up = self.ping(hostname)
        if was_up and not is_up:
            self.notify_down(hostname)
        if not was_up and is_up:
            self.notify_backup(hostname)
        return hostname, is_up

    @staticmethod
    def ping(hostname):
        """ Returns True if the server is responding to ICMP ping, False otherwise. """
        if sys.platform.startswith('linux'):
            response = os.system("ping -c 1 " + hostname + " 2>&1 > /dev/null")
        else:
            response = os.system("ping -n 1 " + hostname + ' | find "TTL=" 2>&1 > NUL')
        return response == 0

    def notify_down(self, hostname):
        """ Sends an email notification that the specified host is down. """
        content = "%s has failed its ping test at %s - monitored by %s. This probably means it's down." % \
                  (hostname,
                   time.strftime("%c"),
                   this_host)
        self.send_email(content)

    def notify_backup(self, hostname):
        """ Sends an email notification that the specified host is back up. """
        content = "%s is now responding to pings again at %s - monitored by %s." % \
                  (hostname,
                   time.strftime("%c"),
                   this_host)
        self.send_email(content)

    @staticmethod
    def send_email(email_content):
        message = "From: %s\nTo: %s\nSubject:Reduction server monitor\n\n%s" % \
                  (email_sender,
                   ", ".join(email_recipients),
                   email_content)
        try:
            s = smtplib.SMTP(email_host, email_port)
            s.sendmail(email_sender, email_recipients, message)
            s.close()
        except Exception as e:
            print("Failed to send emails %s" % message)
            print("Exception %s - %s" % (type(e).__name__, str(e)))


def main():
    Monitor().loop()


if __name__ == '__main__':
    main()
