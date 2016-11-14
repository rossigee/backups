import os, os.path

from backups.notification import BackupNotification

class Flagfile(BackupNotification):
    def __init__(self, config):
        self.filename = config.get('flagfile', 'filename')

    def notify_success(self, source, hostname, filename, stats):
        f = open(self.filename, "w")
        f.write("OK")
        f.close()

    def notify_failure(self, source, hostname, e):
        pass
