import urllib, urllib2
import os, os.path
import json
import logging

from backups.exceptions import BackupException
from backups.notifications import backupnotification
from backups.notifications.notification import BackupNotification

@backupnotification('slack')
class Slack(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'slack')
        self.url = config['url']

    def notify_success(self, source, hostname, filename, stats):
        filesize = stats.getSizeDescription()
        headers = {
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':+1:',
            'text': "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (source.name, source.type, hostname, filesize),
        }
        data = urllib.urlencode({'payload': json.dumps(data)})
        req = urllib2.Request(self.url, data, headers)
        try:
            f = urllib2.urlopen(req)
            response = f.read()
            logging.info("Sent success notification via Slack.")
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Slack success notification: " + contents)

    def notify_failure(self, source, hostname, e):
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':imp:',
            'text': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
        }
        data = urllib.urlencode({'payload': json.dumps(data)})
        req = urllib2.Request(self.url, data)
        try:
            f = urllib2.urlopen(req)
            response = f.read()
            logging.info("Sent failure notification via Slack.")
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Slack failure notification: " + contents)
