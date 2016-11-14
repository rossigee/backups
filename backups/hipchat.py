import urllib, urllib2
import os, os.path

class Hipchat:
    def __init__(self, config):
        self.auth_token = config.get('hipchat', 'auth_token')
        self.room_id = config.get('hipchat', 'room_id')
        self.notify_on_success = False
        if config.has_option('hipchat', 'notify_on_success'):
            self.notify_on_success = config.get('hipchat', 'notify_on_success') == 'True'
        self.notify_on_failure = True
        if config.has_option('hipchat', 'notify_on_failure'):
            self.notify_on_failure = config.get('hipchat', 'notify_on_failure') == 'True'

    def notify_success(self, name, backuptype, hostname, filename, stats):
        if not self.notify_on_success:
            return
        filesize = stats.getSizeDescription()
        data = {
            'room_id': self.room_id,
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (name, backuptype, hostname, filesize),
            'message_format': 'text',
            'notify': 0,
            'color': 'green',
            'auth_token': self.auth_token,
        }
        hipchaturl = "https://api.hipchat.com/v1/rooms/message?%s" % urllib.urlencode(data)
        f = urllib2.urlopen(hipchaturl)
        response = f.read()

    def notify_failure(self, name, backuptype, hostname, e):
        if not self.notify_on_failure:
            return
        data = {
            'room_id': self.room_id,
            'from': 'Backup Agent',
            'message': "Backup of '%s' (%s) on '%s' failed: %s" % (name, backuptype, hostname, str(e)),
            'message_format': 'text',
            'notify': 1,
            'color': 'red',
            'auth_token': self.auth_token,
        }
        hipchaturl = "https://api.hipchat.com/v1/rooms/message?%s" % urllib.urlencode(data)
        f = urllib2.urlopen(hipchaturl)
        response = f.read()
