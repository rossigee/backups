import os, os.path
import datetime
import subprocess
import logging

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

@backupdestination('samba')
class Samba(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        self.sambashare = config['share']
        self.sambahost = config['host']
        self.workgroup = config['workgroup']
        self.username = config['credentials']['username']
        self.password = config['credentials']['password']

    def send(self, id, name, suffix, filename):
        credsfilename = '%s/%s.smbauth' % (self.tmpdir, self.id)
        credsfile = open(credsfilename, 'wb')
        credsfile.write(
            "username = %s\n" \
            "password = %s\n" \
            "workgroup = %s\n" % \
            (self.username, self.password, self.workgroup)
        )
        credsfile.flush()
        credsfile.close()
        os.chmod(credsfilename, 0400)

        try:
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
        finally:
            os.unlink(credsfilename)

    def cleanup(self, id, name, stats):
        logging.warn("Retention control not implemented for Samba destinations yet (PRs welcome!)")
        return
