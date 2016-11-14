import os, os.path
import datetime
import subprocess
import logging

from backups.exceptions import BackupException
from backups.destination import BackupDestination

class Samba(BackupDestination):
    def __init__(self, config):
        self.hostname = config.get('defaults', 'hostname')
        self.sambahost = config.get('samba', 'host')
        self.sambashare = config.get('samba', 'share')
        self.authfile = '/home/backups/.smbauth'

    def send(self, id, name, suffix, filename):
        sambafile = "/%s-%s.%s" % (
            id,
            datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            suffix)
        basename = os.path.basename(filename)
        sambaurl = "smb://%s/%s%s/%s" % (self.sambahost, self.sambashare, sambafile)
        logging.info("Uploading '%s' backup to Samba (%s)..." % (name, sambaurl))
        sharething = "//%s/%s" % (self.sambahost, self.sambashare)
        command = "put %s %s" % (filename, sambafile)
        uploadargs = ['smbclient', '-A', self.authfile, sharething, '-c', command]
        uploadproc = subprocess.Popen(uploadargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        exitcode = uploadproc.wait()
        if exitcode != 0:
            errmsg = "%s%s" % (uploadproc.stdout.read(), uploadproc.stderr.read())
            raise BackupException("Error while uploading: %s" % errmsg)

    def cleanup(self, id, name, suffix, stats):
        logging.error("Retention control not implemented for Samba destinations yet (PRs welcome!)")
        return
