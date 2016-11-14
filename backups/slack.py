import urllib, urllib2
import os, os.path
import json

from backups.notification import BackupNotification

class Slack(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'slack')
        self.url = config.get('slack', 'url')
        #self.username = config.get('slack', 'username')
        #self.channel = config.get('slack', 'channel')

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
        f = urllib2.urlopen(req)

        response = f.read()

    def notify_failure(self, source, hostname, e):
        data = {
            'username': 'Backup Agent',
            'icon_emoji': ':imp:',
            'text': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
        }
        data = urllib.urlencode({'payload': json.dumps(data)})
        req = urllib2.Request(self.url, data)
        f = urllib2.urlopen(req)

        response = f.read()
