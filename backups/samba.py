import os, os.path
import datetime
import subprocess
import logging

from backups.exceptions import BackupException

class Samba:
    def __init__(self, config):
        self.hostname = config.get('defaults', 'hostname')
        self.sambahost = config.get('samba', 'host')
        self.sambashare = config.get('samba', 'share')
        self.authfile = '/home/backups/.smbauth'

    def send(self, filename, name):
        sambadir = "/%s/%s" % (
            self.hostname,
            datetime.datetime.now().strftime("%Y-%m-%d"))
        basename = os.path.basename(filename)
        sambaurl = "smb://%s/%s%s/%s" % (self.sambahost, self.sambashare, sambadir, basename)
        logging.info("Uploading '%s' backup to Samba (%s)..." % (name, sambaurl))
        sharething = "//%s/%s" % (self.sambahost, self.sambashare)
        command = "mkdir /%s; mkdir %s; cd %s; put %s %s" % (self.hostname, sambadir, sambadir, filename, basename)
        uploadargs = ['smbclient', '-A', self.authfile, sharething, '-c', command]
        uploadproc = subprocess.Popen(uploadargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        exitcode = uploadproc.wait()
        if exitcode != 0:
            errmsg = "%s%s" % (uploadproc.stdout.read(), uploadproc.stderr.read())
            raise BackupException("Error while uploading: %s" % errmsg)

