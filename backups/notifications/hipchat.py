import urllib2, json
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
        headers = {
            'Content-type': 'application/json; charset=UTF-8'
        }
        data = {
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (source.name, source.type, hostname, filesize),
            'message_format': 'text',
            'notify': False,
            'color': 'green',
        }
        try:
            r = urllib2.Request(self.url, json.dumps(data), headers)
            f = urllib2.urlopen(r)
            response = f.read()
            logging.info("Sent success notification via Hipchat.")
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Hipchat success notification: " + contents)

    def notify_failure(self, source, hostname, e):
        headers = {
            'Content-type': 'application/json; charset=UTF-8'
        }
        data = {
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
            'message_format': 'text',
            'notify': True,
            'color': 'red',
        }
        try:
            r = urllib2.Request(self.url, json.dumps(data), headers)
            f = urllib2.urlopen(r)
            response = f.read()
            logging.info("Sent failure notification via Hipchat.")
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Hipchat failure notification: " + contents)
