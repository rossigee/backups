import os, os.path
import shutil
import datetime
import logging

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

@backupdestination('local')
class Local(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        self.path = config['path']

    def send(self, id, name, filename):
        destdir = os.path.join(self.path, id, self.runtime.strftime("%Y%m%d%H%M%S"))
        os.makedirs(destdir, exist_ok=True)
        destfile = os.path.join(destdir, os.path.basename(filename))
        logging.info("Copying '%s' backup for '%s' to local path (%s)..." % (name, self.id, destfile))
        try:
            shutil.copy2(filename, destfile)
        except Exception as e:
            raise BackupException("Error while copying (%s): %s" % (self.id, str(e)))
        return destfile

    def cleanup(self, id, name):
        basedir = os.path.join(self.path, id)
        if not os.path.isdir(basedir):
            return []

        candidates = []
        for entry in os.scandir(basedir):
            if entry.is_dir():
                candidates.append([entry.stat().st_mtime, entry.path])
        candidates.sort()

        removable = []
        retained = []
        if self.retention_copies > 0:
            paths = [p for d, p in candidates]
            if len(paths) > self.retention_copies:
                removable = paths[0:(len(paths) - self.retention_copies)]
            retained = paths[(len(paths) - self.retention_copies):]
        if self.retention_days > 0:
            now = datetime.datetime.now()
            for d, path in candidates:
                age = (now - datetime.datetime.fromtimestamp(d)).days
                if age > self.retention_days:
                    removable.append(path)
        for path in removable:
            logging.info("Removing '%s'..." % path)
            shutil.rmtree(path)

        return retained
