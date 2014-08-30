import os, os.path
import datetime
import subprocess
import logging

from backups.exceptions import BackupException

class S3:
    def __init__(self, config):
        self.hostname = config.get('defaults', 'hostname')
        self.bucket = config.get('s3', 'bucket')

    def send(self, filename, name):
        s3location = "s3://%s/%s/%s/%s" % (
            self.bucket,
            self.hostname,
            datetime.datetime.now().strftime("%Y-%m-%d"),
            os.path.basename(filename))
        logging.info("Uploading '%s' backup to S3 (%s)..." % (name, s3location))
        uploadargs = ['s3cmd', 'put', '-rr', '--no-progress', filename, s3location]
        uploadproc = subprocess.Popen(uploadargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        exitcode = uploadproc.wait()
        if exitcode != 0:
            errmsg = "%s%s" % (uploadproc.stdout.read(), uploadproc.stderr.read())
            raise BackupException("Error while uploading: %s" % errmsg)

