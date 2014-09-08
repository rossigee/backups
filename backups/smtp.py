import smtplib
import os, os.path

try:
    from email.mime.text import MIMEText
except:
    from email.MIMEText import MIMEText

from backups.exceptions import BackupException

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

class SMTP:
    def __init__(self, config):
        self.host = "127.0.0.1"
        if config.has_option('smtp', 'host'):
            self.host = config.get('smtp', 'host')
        self.port = 25
        if config.has_option('smtp', 'port'):
            self.port = int(config.get('smtp', 'port'))
        if config.has_option('smtp', 'username'):
            self.username = config.get('smtp', 'username')
        if config.has_option('smtp', 'password'):
            self.password = config.get('smtp', 'password')
        try:
            self.use_tls = int(config.get('smtp', 'use_tls')) == 1
        except:
            self.use_tls = False
        try:
            self.use_ssl = int(config.get('smtp', 'use_ssl')) == 1 
        except:
            self.use_ssl = False
        if config.has_option('smtp', 'success_to'):
            self.success_to = config.get('smtp', 'success_to')
        if config.has_option('smtp', 'failure_to'):
            self.failure_to = config.get('smtp', 'failure_to')

    def notify_success(self, name, backuptype, hostname, filename):
        if 'success_to' not in dir(self) or not self.success_to:
            return
        filesize = sizeof_fmt(os.path.getsize(filename))
        fromaddr = self.success_to
        toaddrs = [fromaddr]
        msg = MIMEText("Successfully backed up %s (%s) [size: %s]" % (name, backuptype, filesize))
        msg['Subject'] = "Backup of %s (%s) on %s was successful" % (name, backuptype, hostname)
        msg['X-Backup-Name'] = hostname
        msg['X-Backup-Type'] = backuptype
        msg['X-Backup-Hostname'] = hostname
        if self.use_ssl:
            server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            server = smtplib.SMTP(self.host, self.port)
        #server.set_debuglevel(1)
        if self.use_tls:
            server.starttls()
            server.ehlo()
        if 'username' in dir(self):
            server.login(self.username, self.password)
        server.sendmail(fromaddr, toaddrs, str(msg))
        server.quit()

    def notify_failure(self, name, backuptype, hostname, e):
        import traceback; traceback.print_exc()
        if 'failure_to' not in dir(self) or not self.failure_to:
            return
        fromaddr = self.failure_to
        toaddrs = [fromaddr]
        msg = MIMEText("Error encountered while backing up %s (%s):\n\n%s" % (name, backuptype, str(e)))
        msg['Subject'] = "ERROR: Backup of %s (%s) on %s failed" % (name, backuptype, hostname)
        msg['X-Backup-Name'] = hostname
        msg['X-Backup-Type'] = backuptype
        msg['X-Backup-Hostname'] = hostname
        if self.use_ssl:
            server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            server = smtplib.SMTP(self.host, self.port)
        #server.set_debuglevel(1)
        if self.use_tls:
            server.starttls()
            server.ehlo()
        if 'username' is dir(self):
            server.login(self.username, self.password)
        server.sendmail(fromaddr, toaddrs, str(msg))
        server.quit()

