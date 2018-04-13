import requests, json
import os, os.path
import logging

from backups.exceptions import BackupException
from backups.notifications import backupnotification
from backups.notifications.notification import BackupNotification

@backupnotification('discord')
class Discord(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'discord')
        self.url = config['url']

    def notify_success(self, source, hostname, filename, stats):
        filesize = stats.getSizeDescription()
        data = {
            'content': "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (source.name, source.type, hostname, filesize),
        }
        try:
            r = requests.post(self.url, data=data)
            r.raise_for_status()
            logging.info("Sent success notification via Discord.")
        except requests.exceptions.HTTPError as err:
            logging.error("Unable to send Discord success notification: " + err)

    def notify_failure(self, source, hostname, e):
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'Mozilla/5.0'
        }
        data = {
            'content': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
        }
        try:
            r = requests.post(self.url, data=data)
            r.raise_for_status()
            logging.info("Sent failure notification via Discord.")
        except requests.exceptions.HTTPError as err:
            logging.error("Unable to send Discord failure notification: " + err)
