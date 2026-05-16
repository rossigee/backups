import os, os.path
import datetime
import logging
import contextlib

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

    def _get_tracer(self):
        if hasattr(self, 'tracer') and self.tracer is not None:
            return self.tracer
        class _NoOpTracer:
            @contextlib.contextmanager
            def start_as_current_span(self, name, **kwargs):
                class _NoOpSpan:
                    def set_attribute(self, *a, **k): pass
                    def record_exception(self, *a, **k): pass
                    def set_status(self, *a, **k): pass
                yield _NoOpSpan()
        return _NoOpTracer()

    def _get_client(self):
        return Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

    def send(self, id, name, filename):
        with self._get_tracer().start_as_current_span("minio_upload") as span:
            span.set_attribute("destination.id", self.id)
            span.set_attribute("minio.endpoint", self.endpoint)
            span.set_attribute("minio.bucket", self.bucket)
            span.set_attribute("source.id", id)
            span.set_attribute("upload.file", filename)
            
            object_name = "%s/%s/%s" % (id, self.runtime.strftime("%Y%m%d%H%M%S"), os.path.basename(filename))
            location = "%s/%s/%s" % (self.endpoint, self.bucket, object_name)
            logging.info("Uploading '%s' backup for '%s' to Minio (%s)..." % (name, self.id, location))
            try:
                client = self._get_client()
                client.fput_object(self.bucket, object_name, filename)
                span.set_attribute("minio.object", object_name)
            except S3Error as e:
                span.record_exception(BackupException("Error while uploading (%s): %s" % (self.id, str(e))))
                raise BackupException("Error while uploading (%s): %s" % (self.id, str(e)))
            return location

    def cleanup(self, id, name):
        with self._get_tracer().start_as_current_span("minio_cleanup") as span:
            span.set_attribute("destination.id", self.id)
            span.set_attribute("minio.endpoint", self.endpoint)
            span.set_attribute("minio.bucket", self.bucket)
            span.set_attribute("source.id", id)
            span.set_attribute("retention.copies", self.retention_copies)
            span.set_attribute("retention.days", self.retention_days)
            
            logging.info("Clearing down older '%s' backups for '%s' from Minio..." % (name, self.id))
            try:
                client = self._get_client()
                objects = list(client.list_objects(self.bucket, prefix="%s/" % id, recursive=True))
            except S3Error as e:
                span.record_exception(BackupException("Error listing Minio bucket (%s): %s" % (self.id, str(e))))
                raise BackupException("Error listing Minio bucket (%s): %s" % (self.id, str(e)))

            candidates = [[obj.last_modified, obj.object_name] for obj in objects]
            candidates.sort()
            span.set_attribute("object.count", len(candidates))

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
            span.set_attribute("removed.count", len(removable))
            span.set_attribute("retained.count", len(retained))

            return retained
