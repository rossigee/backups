import os, os.path
import datetime
import logging

from minio import Minio
from minio.error import S3Error

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

@backupdestination('minio')
class MinioDestination(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        self.bucket = config['bucket']
        self.endpoint = config['endpoint']
        self.access_key = config['credentials']['access_key']
        self.secret_key = config['credentials']['secret_key']
        self.secure = bool(config.get('secure', True))

    def _get_client(self):
        return Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

    def send(self, id, name, filename):
        object_name = "%s/%s/%s" % (id, self.runtime.strftime("%Y%m%d%H%M%S"), os.path.basename(filename))
        location = "%s/%s/%s" % (self.endpoint, self.bucket, object_name)
        logging.info("Uploading '%s' backup for '%s' to Minio (%s)..." % (name, self.id, location))
        try:
            client = self._get_client()
            client.fput_object(self.bucket, object_name, filename)
        except S3Error as e:
            raise BackupException("Error while uploading (%s): %s" % (self.id, str(e)))
        return location

    def cleanup(self, id, name):
        logging.info("Clearing down older '%s' backups for '%s' from Minio..." % (name, self.id))
        try:
            client = self._get_client()
            objects = list(client.list_objects(self.bucket, prefix="%s/" % id, recursive=True))
        except S3Error as e:
            raise BackupException("Error listing Minio bucket (%s): %s" % (self.id, str(e)))

        candidates = [[obj.last_modified, obj.object_name] for obj in objects]
        candidates.sort()

        removable = []
        retained = []
        if self.retention_copies > 0:
            names = [n for d, n in candidates]
            if len(names) > self.retention_copies:
                removable = names[0:(len(names) - self.retention_copies)]
            retained = names[(len(names) - self.retention_copies):]
        if self.retention_days > 0:
            now = datetime.datetime.now(datetime.timezone.utc)
            for d, n in candidates:
                age = (now - d).days
                if age > self.retention_days:
                    removable.append(n)
        for object_name in removable:
            logging.info("Removing '%s'..." % object_name)
            try:
                client.remove_object(self.bucket, object_name)
            except S3Error as e:
                logging.warning("Failed to remove '%s': %s" % (object_name, str(e)))

        return retained
