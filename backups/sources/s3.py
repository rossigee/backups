import os
import fnmatch
import logging
import tarfile
import io

from minio import Minio

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException


@backupsource('s3')
class S3(BackupSource):
    def __init__(self, config, type="S3"):
        BackupSource.__init__(self, config, type, "tar.gpg")
        self.bucket = config['bucket']
        self.endpoint = config.get('endpoint')
        self.region = config.get('region', 'us-east-1')
        self.secure = bool(config.get('secure', True))
        # credentials may be top-level or nested
        creds = config.get('credentials', {})
        self.access_key = config.get('access_key') or creds.get('access_key') or config.get('accessKey')
        self.secret_key = config.get('secret_key') or creds.get('secret_key') or config.get('secretKey')
        self.prefix = config.get('prefix', '').lstrip('/')
        if self.prefix and not self.prefix.endswith('/'):
            # keep as prefix without requiring trailing slash; list will handle
            pass
        self.excludes = []
        if 'excludes' in config:
            self.excludes = config['excludes']
        elif 'exclude' in config:
            self.excludes = config['exclude']

    def _get_client(self):
        if not self.endpoint:
            raise BackupException("S3 source requires 'endpoint'")
        if not self.access_key or not self.secret_key:
            raise BackupException("S3 source requires credentials")
        return Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
            region=self.region,
        )

    def dump(self):
        tarfilename = '%s/%s.tar' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s) from s3://%s/%s ...", self.name, self.type, self.bucket, self.prefix or "")
        client = self._get_client()
        try:
            objects = list(client.list_objects(self.bucket, prefix=self.prefix, recursive=True))
        except Exception as e:
            raise BackupException("Error listing s3 bucket %s/%s: %s" % (self.bucket, self.prefix, e))

        if not objects:
            logging.warning("No objects found in s3://%s/%s", self.bucket, self.prefix)

        with tarfile.open(tarfilename, 'w') as tar:
            for obj in objects:
                object_name = obj.object_name
                # arcname is object_name relative to prefix, or full name if no prefix
                if self.prefix:
                    if object_name.startswith(self.prefix):
                        arcname = object_name[len(self.prefix):].lstrip('/')
                    else:
                        arcname = object_name
                else:
                    arcname = object_name
                if not arcname:
                    continue
                # excludes
                excluded = any(
                    fnmatch.fnmatch(arcname, ex) or fnmatch.fnmatch(os.path.basename(arcname), ex)
                    for ex in self.excludes
                )
                if excluded:
                    continue
                # skip directories (MinIO may return 0-byte objects with trailing slash)
                if object_name.endswith('/') and obj.size == 0:
                    continue
                try:
                    # Use get_object to stream
                    response = client.get_object(self.bucket, object_name)
                    try:
                        # Need to handle streaming without knowing size? Use object size
                        info = tarfile.TarInfo(name=arcname)
                        info.size = obj.size
                        # Use last_modified as mtime if available
                        if obj.last_modified:
                            info.mtime = int(obj.last_modified.timestamp())
                        info.mode = 0o644
                        tar.addfile(info, response)
                    finally:
                        response.close()
                        response.release_conn()
                except Exception as e:
                    raise BackupException("Error downloading s3://%s/%s: %s" % (self.bucket, object_name, e))
        return [tarfilename]
