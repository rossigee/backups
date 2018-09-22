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

    @staticmethod
    def pretty_print(seconds):
        sec = 0 if not seconds else seconds
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    def _send(self, type, payload):
        headers = {
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        data = urllib.urlencode({'payload': json.dumps(payload)})
        req = urllib2.Request(self.url, data, headers)
        try:
            f = urllib2.urlopen(req)
            response = f.read()
            logging.info('Sent %s notification via Slack.' % type)
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error('Unable to send Slack %s notification: ' % type + contents)

    def notify_start(self, source, hostname):
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':+1:',
            'text': "Backup of '%s' (%s) on '%s' beginning." % (source.name, source.type, hostname),
        }
        self._send('start', data)

    def notify_success(self, source, hostname, filename, stats):
        filesize = stats.getSizeDescription()
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':+1:',
            'text': "Backup of '%s' (%s) on '%s' was successful [size: %s].\nTimes: backup %s, dump %s" %
                    (source.name, source.type, hostname, filesize,
                     Slack.pretty_print(stats.dumptime), Slack.pretty_print(stats.uploadtime)),
        }
        self._send('success', data)

    def notify_failure(self, source, hostname, e):
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':imp:',
            'text': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
        }
        self._send('failure', data)

