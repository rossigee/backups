import urllib, urllib2
import os, os.path
import json
import logging

from backups.notification import BackupNotification

class Telegram(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'telegram')
        self.api_token = config.get('telegram', 'api_token')
        self.chat_id = config.get('telegram', 'chat_id')

    def notify_success(self, source, hostname, filename, stats):
        filesize = stats.getSizeDescription()
        message = "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (source.name, source.type, hostname, filesize)
        url = "https://api.telegram.org/bot" + self.api_token + "/sendMessage"
        data = urllib.urlencode({
            'chat_id': self.chat_id,
            'text': message
        })
        try:
            f = urllib2.urlopen(url, data)
            response = f.read()
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Telegram notification: " + contents)

    def notify_failure(self, source, hostname, e):
        message = "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
        url = "https://api.telegram.org/bot" + self.api_token + "/sendMessage"
        data = urllib.urlencode({
            'chat_id': self.chat_id,
            'text': message
        })
        try:
            f = urllib2.urlopen(url, data)
            response = f.read()
        except urllib2.HTTPError, error:
            contents = error.read()
            logging.error("Unable to send Telegram notification: " + contents)
