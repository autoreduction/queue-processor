import os, sys, time, smtplib

# The hosts to keep tabs on
monitoredHosts = ["reduce.isis.cclrc.ac.uk"]

# Settings for the email notification
emailHost = 'exchsmtp.stfc.ac.uk'
emailPort = 25
emailRecipients = ['isisreduce@stfc.ac.uk']
emailSender = 'monitor@autoreduce.isis.cclrc.ac.uk'
thisHost = 'autoreduce.isis.cclrc.ac.uk'

class Monitor(object):
    def __init__(self, hostnameList=monitoredHosts):
        """ hostnameList should be a list of hostname strings; hostList will be a zip of these names and whether they passed their last ping test. """
        self.hostList = [(hostname, True) for hostname in hostnameList]
        
    def loop(self):
        """ Check all hosts once every minute and update their statuses. """
        while True:
            self.hostList = [self.check(*tup) for tup in self.hostList]
            time.sleep(60)
        
    def check(self, hostname, wasUp):
        """ Ping the given host, and if its status has changed, send a notification; returns its new state. """
        isUp = self.ping(hostname)
        if wasUp and not isUp:
            self.notifyDown(hostname)
        if not wasUp and isUp:
            self.notifyBackUp(hostname)
        return (hostname, isUp)
            
    def ping(self, hostname):
        """ Returns True if the server is responding to ICMP ping, False otherwise. """
        if sys.platform.startswith('linux'):
            response = os.system("ping -c 1 " + hostname + " 2>&1 > /dev/null")
        else:
            response = os.system("ping -n 1 " + hostname + ' | find "TTL=" 2>&1 > NUL')
        return response == 0
    
    def notifyDown(self, hostname):
        """ Sends an email notification that the specified host is down. """
        content = "%s has failed its ping test at %s - monitored by %s. This probably means it's down." % (hostname, time.strftime("%c"), thisHost)
        self.sendEmail(content)
            
    def notifyBackUp(self, hostname):
        """ Sends an email notification that the specified host is back up. """
        content = "%s is now responding to pings again at %s - monitored by %s." % (hostname, time.strftime("%c"), thisHost)
        self.sendEmail(content)
    
    def sendEmail(self, emailContent):
        message = "From: %s\nTo: %s\nSubject:Reduction server monitor\n\n%s" % (emailSender, ", ".join(emailRecipients), emailContent)
        try:
            s = smtplib.SMTP(emailHost, emailPort)
            s.sendmail(emailSender, emailRecipients, message)
            s.close()
        except Exception as e:
            print("Failed to send emails %s" % message)
            print("Exception %s - %s" % (type(e).__name__, str(e)))
        
def main():
    Monitor().loop()
if __name__ == '__main__':
    main()