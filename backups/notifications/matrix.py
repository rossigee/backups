import urllib, urllib2
import json
import logging

from backups.exceptions import BackupException
from backups.notifications import backupnotification
from backups.notifications.notification import BackupNotification

@backupnotification('matrix')
class Matrix(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'matrix')
        self.url = "{}/_matrix/client/r0/rooms/{}/send/m.room.message?access_token={}".format(
            config['url'],
            config['room_id'],
            config['access_token']
        )

    def _msg(self, text):
        headers = {
            'Content-type': 'application/json; charset=UTF-8',
        }
        data = {
            'msgtype': 'm.text',
            'body': text,
        }
        req = urllib2.Request(self.url, data=json.dumps(data), headers=headers)
        return urllib2.urlopen(req)

    def notify_success(self, source, hostname, filename, stats):
        filesize = stats.getSizeDescription()
        text = "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (source.name, source.type, hostname, filesize)
        try:
            f = self._msg(text)
            logging.info("Sent success notification via Matrix.")
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Matrix success notification: " + contents)

    def notify_failure(self, source, hostname, e):
        text = "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e))
        try:
            f = self._msg(text)
            logging.info("Sent failure notification via Matrix.")
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Matrix failure notification: " + contents)
