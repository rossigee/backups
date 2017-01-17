import smtplib
import os, os.path

try:
    from email.mime.text import MIMEText
except:
    from email.MIMEText import MIMEText

from backups.exceptions import BackupException
from backups.notification import BackupNotification

class SMTP(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'smtp')
        try:
            self.host = config.get('smtp', 'host')
        except:
            self.host = config.get_or_envvar('defaults', 'host', 'SMTP_HOST')
        try:
            self.port = int(config.get('smtp', 'port'))
        except:
            self.port = int(config.get_or_envvar('defaults', 'port', 'SMTP_PORT'))
        try:
            self.username = config.get('smtp', 'username')
        except:
            self.username = config.get_or_envvar('defaults', 'username', 'SMTP_USERNAME')
        try:
            self.password = config.get('smtp', 'password')
        except:
            self.password = config.get_or_envvar('defaults', 'password', 'SMTP_PASSWORD')
        try:
            self.use_tls = int(config.get('smtp', 'use_tls')) == 1
        except:
            self.use_tls = int(config.get_or_envvar('defaults', 'use_tls', 'SMTP_USE_TLS')) == 1
        try:
            self.use_ssl = int(config.get('smtp', 'use_ssl')) == 1
        except:
            self.use_ssl = int(config.get_or_envvar('defaults', 'use_ssl', 'SMTP_USE_SSL')) == 1
        try:
            self.success_to = config.get('smtp', 'success_to')
        except:
            self.success_to = config.get_or_envvar('defaults', 'success_to', 'SMTP_SUCCESS_TO')
        try:
            self.failure_to = config.get('smtp', 'failure_to')
        except:
            self.failure_to = config.get_or_envvar('defaults', 'failure', 'SMTP_FAILURE_TO')
        try:
            self.debug = int(config.get('smtp', 'debug')) == 1
        except:
            try:
                self.debug = int(config.get_or_envvar('defaults', 'debug', 'SMTP_DEBUG')) == 1
            except:
                self.debug = False

    def notify_success(self, source, hostname, filename, stats):
        if 'success_to' not in dir(self) or not self.success_to:
            return
        filesize = stats.getSizeDescription()
        fromaddr = self.success_to
        toaddrs = [fromaddr]
        msg = MIMEText("Successfully backed up %s (%s) [size: %s]" % (source.name, source.type, filesize))
        msg['Subject'] = "Backup of %s (%s) on %s was successful" % (source.name, source.type, hostname)
        msg['X-Backup-Id'] = source.id
        msg['X-Backup-Type'] = source.type
        msg['X-Backup-Hostname'] = hostname
        if self.use_ssl:
            server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            server = smtplib.SMTP(self.host, self.port)
        if self.debug:
            server.set_debuglevel(1)
        if self.use_tls:
            server.starttls()
            server.ehlo()
        if 'username' in dir(self):
            server.login(self.username, self.password)
        server.sendmail(fromaddr, toaddrs, msg.as_string())
        server.quit()

    def notify_failure(self, source, hostname, e):
        import traceback; traceback.print_exc()
        if 'failure_to' not in dir(self) or not self.failure_to:
            return
        fromaddr = self.failure_to
        toaddrs = [fromaddr]
        msg = MIMEText("Error encountered while backing up %s (%s):\n\n%s" % (source.name, source.type, str(e)))
        msg['Subject'] = "ERROR: Backup of %s (%s) on %s failed" % (source.name, source.type, hostname)
        msg['X-Backup-Id'] = source.id
        msg['X-Backup-Type'] = source.type
        msg['X-Backup-Hostname'] = hostname
        if self.use_ssl:
            server = smtplib.SMTP_SSL(self.host, self.port)
        else:
            server = smtplib.SMTP(self.host, self.port)
        if self.debug:
            server.set_debuglevel(1)
        if self.use_tls:
            server.starttls()
            server.ehlo()
        if 'username' in dir(self):
            server.login(self.username, self.password)
        server.sendmail(fromaddr, toaddrs, msg.as_string())
        server.quit()
