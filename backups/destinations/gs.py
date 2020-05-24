import os, os.path
import subprocess
import logging
import datetime

from google.cloud import storage
from google.api_core.exceptions import BadRequest

from dateutil import parser, tz

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

@backupdestination('gs')
class GS(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        # TODO: Finish this off...
        self.gcs_creds_path = config['gcs_creds_path']
        self.bucket = config['bucket']

    def send(self, id, name, filename):
        gslocation = "gs://%s/%s/%s/%s" % (
            self.bucket,
            id,
            self.runtime.strftime("%Y%m%d%H%M%S"),
            os.path.basename(filename))
        logging.info("Uploading '%s' backup for '%s' to GS (%s)..." % (name, self.id, gslocation))
        uploadargs = ['gsutil', '-q', 'cp', filename, gslocation]
        uploadenv = os.environ.copy()
        uploadproc = subprocess.Popen(uploadargs, stderr=subprocess.PIPE, env=uploadenv)
        uploadproc.wait()
        exitcode = uploadproc.returncode
        errmsg = uploadproc.stderr.read()
        if exitcode != 0:
            raise BackupException("Error while uploading (%s): %s" % (self.id, errmsg))

        return [gslocation, ]

    def cleanup(self, id, name):
        gslocation = "gs://%s/%s" % (self.bucket, id)
        logging.info("Clearing down older '%s' backups for '%s' from GS (%s)..." % (name, self.id, gslocation))

        client = storage.Client.from_service_account_json(self.gcs_creds_path)
        bucket = client.get_bucket(self.bucket)

        # Gather list of potentials first
        candidates = []
        for key in bucket.list(prefix="%s/" % id):
            parsed_date = parser.parse(key.last_modified)
            candidates.append([parsed_date, key.name])
        candidates.sort()

        # Loop and purge unretainable copies
        removable_names = []
        retained_copies = []
        if self.retention_copies > 0:
            names = [name for d, name in candidates]
            if len(names) > self.retention_copies:
                removable_names = names[0:(len(names) - self.retention_copies)]
            else:
                retained_copies = names[(len(names) - self.retention_copies):]
        if self.retention_days > 0:
            for d, name in candidates:
                days = (datetime.datetime.now(tz.tzutc()) - d).days
                if days > self.retention_days:
                    removable_names.append(name)
        for name in removable_names:
            logging.info("Removing '%s'..." % name)
            bucket.get_key(name).delete()

        # Return list of retained copies
        return retained_copies
