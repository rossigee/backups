import urllib, urllib2
import os, os.path
import json
import logging

class Telegram:
    def __init__(self, config):
        self.api_token = config.get('telegram', 'api_token')
        self.chat_id = config.get('telegram', 'chat_id')

        self.notify_on_success = False
        if config.has_option('telegram', 'notify_on_success'):
            self.notify_on_success = config.get('telegram', 'notify_on_success') == 'True'
        self.notify_on_failure = True
        if config.has_option('telegram', 'notify_on_failure'):
            self.notify_on_failure = config.get('telegram', 'notify_on_failure') == 'True'

    def notify_success(self, name, backuptype, hostname, filename, stats):
        if not self.notify_on_success:
            return
        filesize = stats.getSizeDescription()
        message = "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (name, backuptype, hostname, filesize)
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

    def notify_failure(self, name, backuptype, hostname, e):
        if not self.notify_on_failure:
            return
        message = "Backup of '%s' (%s) on '%s' failed: %s" % (name, backuptype, hostname, str(e)),
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
