import urllib, urllib2
import os, os.path
import logging

from backups.exceptions import BackupException
from backups.notifications import backupnotification
from backups.notifications.notification import BackupNotification

@backupnotification('hipchat')
class Hipchat(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'hipchat')
        self.url = config['url']

    def notify_success(self, source, hostname, filename, stats):
        filesize = stats.getSizeDescription()
        data = {
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (source.name, source.type, hostname, filesize),
            'message_format': 'text',
            'notify': 0,
            'color': 'green',
        }
        try:
            f = urllib2.urlopen(self.url, urllib.urlencode(data))
            response = f.read()
            logging.info("Sent success notification via Hipchat.")
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Hipchat success notification: " + contents)

    def notify_failure(self, source, hostname, e):
        data = {
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
            'message_format': 'text',
            'notify': 1,
            'color': 'red',
        }
        try:
            f = urllib2.urlopen(self.url, urllib.urlencode(data))
            response = f.read()
            logging.info("Sent failure notification via Hipchat.")
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Hipchat failure notification: " + contents)
