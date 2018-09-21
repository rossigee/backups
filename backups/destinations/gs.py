import os, os.path
import subprocess
import logging
import datetime

import boto
from dateutil import parser, tz

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

@backupdestination('gs')
class GS(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        self.bucket = config['bucket']

    def send(self, id, name, filename):
        gslocation = "gs://%s/%s/%s/%s" % (
            self.bucket,
            id,
            self.runtime.strftime("%Y%m%d%H%M%S"),
            os.path.basename(filename))
        logging.info("Uploading '%s' backup to GS (%s)..." % (name, gslocation))
        uploadargs = ['gsutil', '-q', 'cp', filename, gslocation]
        uploadenv = os.environ.copy()
        uploadproc = subprocess.Popen(uploadargs, stderr=subprocess.PIPE, env=uploadenv)
        uploadproc.wait()
        exitcode = uploadproc.returncode
        errmsg = uploadproc.stderr.read()
        if exitcode != 0:
            raise BackupException("Error while uploading: %s" % errmsg)

    def cleanup(self, id, name, stats):
        gslocation = "gs://%s/%s" % (self.bucket, id)
        logging.info("Clearing down older '%s' backups from GS (%s)..." % (name, gslocation))

        uri = boto.storage_uri(self.bucket, 'gs')
        bucket = uri.get_bucket()

        # Gather list of potentials first
        candidates = []
        for key in bucket.list(prefix="%s/" % id):
            parsed_date = parser.parse(key.last_modified)
            candidates.append([parsed_date, key.name])
        candidates.sort()

        # Loop and purge unretainable copies
        removable_names = []
        if self.retention_copies > 0:
            names = [name for d, name in candidates]
            if len(names) > self.retention_copies:
                removable_names = names[0:(len(names) - self.retention_copies)]
        if self.retention_days > 0:
            for d, name in candidates:
                days = (datetime.datetime.now(tz.tzutc()) - d).days
                if days > self.retention_days:
                    removable_names.append(name)
        for name in removable_names:
            logging.info("Removing '%s'..." % name)
            bucket.get_key(name).delete()

        # Return number of copies left
        stats.retained_copies = len(candidates) - len(removable_names)
