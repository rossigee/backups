import os, os.path
import datetime
import subprocess
import logging

import boto.s3

import dateutil.parser

from backups.exceptions import BackupException
from backups.destination import BackupDestination

class S3(BackupDestination):
    def __init__(self, config):
        self.hostname = config.get('defaults', 'hostname')
        self.bucket = config.get('s3', 'bucket')

        self.az = config.get('s3', 'availability_zone')
        try:
            self.aws_key = config.get('s3', 'aws_access_key_id')
        except:
            self.aws_key = config.get('defaults', 'aws_access_key_id')
        try:
            self.aws_secret = config.get('s3', 'aws_secret_access_key')
        except:
            self.aws_secret = config.get('defaults', 'aws_secret_access_key')

        try:
            self.retention_copies = int(config.get('s3', 'retention_copies'))
        except:
            self.retention_copies = 0

        try:
            self.retention_days = int(config.get('s3', 'retention_days'))
        except:
            self.retention_days = 0

    def send(self, id, name, suffix, filename):
        s3location = "s3://%s/%s-%s.%s" % (
            self.bucket,
            id,
            datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            suffix)
        logging.info("Uploading '%s' backup to S3 (%s)..." % (name, s3location))
        uploadargs = ['aws', 's3', 'cp', filename, s3location]
        uploadproc = subprocess.Popen(uploadargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        exitcode = uploadproc.wait()
        if exitcode != 0:
            errmsg = "%s%s" % (uploadproc.stdout.read(), uploadproc.stderr.read())
            raise BackupException("Error while uploading: %s" % errmsg)

    def cleanup(self, id, name, suffix, stats):
        s3location = "s3://%s/%s" % (self.bucket, id)
        logging.info("Clearing down older '%s' backups from S3 (%s)..." % (name, s3location))

        # Gather list of potentials first
        s3conn = boto.s3.connect_to_region(self.az,
            aws_access_key_id=self.aws_key,
            aws_secret_access_key=self.aws_secret)
        bucket = s3conn.get_bucket(self.bucket)
        candidates = []
        for key in bucket.list(prefix=id):
            if not key.name.endswith(suffix):
                continue
            parsed_date = dateutil.parser.parse(key.last_modified)
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
                days = (d - timedate.timedate.now()).days
                if days > self.retention_days:
                    removable_names.append(name)
        for name in removable_names:
            logging.info("Removing '%s'..." % name)
            bucket.get_key(name).delete()

        # Return number of copies left
        stats.retained_copies = len(candidates) - len(removable_names)
