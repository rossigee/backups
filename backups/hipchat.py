import urllib, urllib2
import os, os.path

from backups.notification import BackupNotification

class Hipchat(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'hipchat')
        self.auth_token = config.get('hipchat', 'auth_token')
        self.room_id = config.get('hipchat', 'room_id')

    def notify_success(self, source, hostname, filename, stats):
        filesize = stats.getSizeDescription()
        data = {
            'room_id': self.room_id,
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (source.name, source.type, hostname, filesize),
            'message_format': 'text',
            'notify': 0,
            'color': 'green',
            'auth_token': self.auth_token,
        }
        hipchaturl = "https://api.hipchat.com/v1/rooms/message?%s" % urllib.urlencode(data)
        f = urllib2.urlopen(hipchaturl)
        response = f.read()

    def notify_failure(self, source, hostname, e):
        data = {
            'room_id': self.room_id,
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' failed: %s" % (source.name, source.type, hostname, str(e)),
            'message_format': 'text',
            'notify': 1,
            'color': 'red',
            'auth_token': self.auth_token,
        }
        hipchaturl = "https://api.hipchat.com/v1/rooms/message?%s" % urllib.urlencode(data)
        f = urllib2.urlopen(hipchaturl)
        response = f.read()
