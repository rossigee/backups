import urllib, urllib2
import os, os.path
import json

def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

class Slack:
    def __init__(self, config):
        self.url = config.get('slack', 'url')
        #self.username = config.get('slack', 'username')
        #self.channel = config.get('slack', 'channel')
        self.notify_on_success = False
        if config.has_option('slack', 'notify_on_success'):
            self.notify_on_success = config.get('slack', 'notify_on_success') == 'True'
        self.notify_on_failure = True
        if config.has_option('slack', 'notify_on_failure'):
            self.notify_on_failure = config.get('slack', 'notify_on_failure') == 'True'
    
    def notify_success(self, name, backuptype, hostname, filename):
        if not self.notify_on_success:
            return
        filesize = sizeof_fmt(os.path.getsize(filename))
        headers = {
            'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        data = {
            'username': 'Backup Agent',
            'text': "Backup of '%s' (%s) on '%s' was successful [size: %s]." % (name, backuptype, hostname, filesize),
        }
        data = urllib.urlencode({'payload': json.dumps(data)})
        req = urllib2.Request(self.url, data, headers)
        f = urllib2.urlopen(req)
        
        response = f.read()
    
    def notify_failure(self, name, backuptype, hostname, e):
        if not self.notify_on_failure:
            return
        data = {
            'username': 'Backup Agent',
            'text': "Backup of '%s' (%s) on '%s' failed: %s" % (name, backuptype, hostname, str(e)),
        }
        data = urllib.urlencode({'payload': json.dumps(data)})
        req = urllib2.Request(self.url, data)
        f = urllib2.urlopen(req)
        
        response = f.read()
