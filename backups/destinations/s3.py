import os, os.path
import subprocess
import logging

import boto3

import dateutil.parser

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

@backupdestination('s3')
class S3(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        self.bucket = config['bucket']
        self.region = config['region']

        self.aws_key = None
        self.aws_secret = None
        if 'credentials' in config:
            self.aws_key = config['credentials']['aws_access_key_id']
            self.aws_secret = config['credentials']['aws_secret_access_key']

    def send(self, id, name, filename):
        s3location = "s3://%s/%s/%s/%s" % (
            self.bucket,
            id,
            self.runtime.strftime("%Y%m%d%H%M%S"),
            os.path.basename(filename))
        logging.info("Uploading '%s' backup to S3 (%s)..." % (name, s3location))

        uploadargs = ['aws', 's3', 'cp', '--only-show-errors', filename, s3location]
        uploadenv = os.environ.copy()
        if self.aws_key is not None:
            uploadenv['AWS_ACCESS_KEY_ID'] = self.aws_key
            uploadenv['AWS_SECRET_ACCESS_KEY'] = self.aws_secret
            uploadenv['AWS_DEFAULT_REGION'] = self.region
        uploadproc = subprocess.Popen(uploadargs, stderr=subprocess.PIPE, env=uploadenv)
        uploadproc.wait()
        exitcode = uploadproc.returncode
        errmsg = uploadproc.stderr.read()
        if exitcode != 0:
            raise BackupException("Error while uploading: %s" % errmsg)

    def _boto_kwargs(self):
        kwargs = dict()
        if self.aws_key is not None:
            kwargs['aws_access_key_id'] = self.aws_key
            kwargs['aws_secret_access_key'] = self.aws_secret
        return kwargs

    def cleanup(self, id, name, stats):
        s3location = "s3://%s/%s" % (self.bucket, id)
        logging.info("Clearing down older '%s' backups from S3 (%s)..." % (name, s3location))

        # Gather list of potentials first
        kwargs = self._boto_kwargs()
        s3 = boto3.resource('s3', **kwargs)
        bucket = s3.Bucket(self.bucket)
        candidates = []
        for obj in bucket.objects.filter(Prefix="%s/" % id):
            candidates.append([obj.last_modified, obj.key])
        candidates.sort()

        # Loop and purge unretainable copies
        removable_names = []
        if self.retention_copies > 0:
            names = [name for d, name in candidates]
            if len(names) > self.retention_copies:
                removable_names = names[0:(len(names) - self.retention_copies)]
        if self.retention_days > 0:
            for d, name in candidates:
                days = (d - timedate.timedate.now()).days
                if days > self.retention_days:
                    removable_names.append(name)
        for name in removable_names:
            logging.info("Removing '%s'..." % name)
            obj = s3.Object(bucket_name=self.bucket, key=name)
            obj.delete()

        # Return number of copies left
        stats.retained_copies = len(candidates) - len(removable_names)
