import os, os.path
import json
import requests

import logging

from backups.exceptions import BackupException
from backups.notifications import backupnotification
from backups.notifications.notification import BackupNotification


@backupnotification('slack')
class Slack(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'slack')
        self.url = config['url']

    @staticmethod
    def pretty_print(seconds):
        sec = 0 if not seconds else seconds
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    def _send(self, notification_type, payload):
        try:
            r = requests.post(self.url, data=payload)
            r.raise_for_status()
            logging.info("Sent failure notification via Slack.")
        except requests.exceptions.HTTPError as err:
            logging.error("Unable to send Slack failure notification: " + err)

    def notify_start(self, source, hostname):
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':+1:',
            'text': "Backup of '%s' (%s) on '%s' beginning." % (source.name, source.type, hostname),
        }
        self._send('start', data)

    def notify_success(self, source, hostname, filename, stats):
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':+1:',
            'text': "Backup of '%s' (%s) on '%s' was successful [size: %s] in %s [backup %s, encrypt %s, upload %s]." %
                    (source.name, source.type, hostname, stats.getSizeDescription(), Slack.pretty_print(stats.dumptime + stats.uploadtime),
                     Slack.pretty_print(stats.dumptime_dump), Slack.pretty_print(stats.dumptime_encrypt), Slack.pretty_print(stats.uploadtime)),
        }
        self._send('success', data)

    def notify_failure(self, source, hostname, e):
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':imp:',
            'text': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
        }
        self._send('failure', data)
