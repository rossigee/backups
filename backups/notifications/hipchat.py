import json
import os, os.path
import requests

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
            'notify': False,
            'color': 'green',
        }
        try:
            r = requests.post(self.url, data=data)
            r.raise_for_status()
            logging.info("Sent success notification via Hipchat.")
        except requests.exceptions.HTTPError as err:
            logging.error("Unable to send Hipchat success notification: " + err)

    def notify_failure(self, source, hostname, e):
        data = {
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
            'message_format': 'text',
            'notify': True,
            'color': 'red',
        }
        try:
            r = requests.post(self.url, data=data)
            r.raise_for_status()
            logging.info("Sent failure notification via Hipchat.")
        except requests.exceptions.HTTPError as err:
            logging.error("Unable to send Hipchat failure notification: " + err)
