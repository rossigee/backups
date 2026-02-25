import os, os.path
import datetime
import logging

from b2sdk.v2 import InMemoryAccountInfo, B2Api

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

@backupdestination('b2')
class B2(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        self.bucket_name = config['bucket']
        self.application_key_id = config['credentials']['application_key_id']
        self.application_key = config['credentials']['application_key']

    def _get_bucket(self):
        info = InMemoryAccountInfo()
        api = B2Api(info)
        api.authorize_account("production", self.application_key_id, self.application_key)
        return api.get_bucket_by_name(self.bucket_name)

    def send(self, id, name, filename):
        remote_name = "%s/%s/%s" % (id, self.runtime.strftime("%Y%m%d%H%M%S"), os.path.basename(filename))
        logging.info("Uploading '%s' backup for '%s' to B2 (%s/%s)..." % (name, self.id, self.bucket_name, remote_name))
        try:
            bucket = self._get_bucket()
            bucket.upload_local_file(local_file=filename, file_name=remote_name)
        except Exception as e:
            raise BackupException("Error while uploading (%s): %s" % (self.id, str(e)))
        return "b2://%s/%s" % (self.bucket_name, remote_name)

    def cleanup(self, id, name):
        logging.info("Clearing down older '%s' backups for '%s' from B2..." % (name, self.id))
        try:
            bucket = self._get_bucket()
            candidates = []
            for file_version, _ in bucket.ls(folder_to_list="%s/" % id, recursive=True):
                candidates.append([file_version.upload_timestamp, file_version])
            candidates.sort(key=lambda x: x[0])
        except Exception as e:
            raise BackupException("Error listing B2 bucket (%s): %s" % (self.id, str(e)))

        removable = []
        retained = []
        if self.retention_copies > 0:
            items = [f for d, f in candidates]
            if len(items) > self.retention_copies:
                removable = items[0:(len(items) - self.retention_copies)]
            retained = [f.file_name for f in items[(len(items) - self.retention_copies):]]
        if self.retention_days > 0:
            now_ms = datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000
            for ts, file_version in candidates:
                age_days = (now_ms - ts) / (1000 * 86400)
                if age_days > self.retention_days:
                    removable.append(file_version)
        for file_version in removable:
            logging.info("Removing '%s'..." % file_version.file_name)
            try:
                file_version.delete()
            except Exception as e:
                logging.warning("Failed to remove '%s': %s" % (file_version.file_name, str(e)))

        return retained
