import os, os.path
import subprocess
import logging

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('folder-ssh')
class FolderSSH(BackupSource):
    def __init__(self, config, type="FolderSSH"):
        BackupSource.__init__(self, config, type, "tar.gpg")
        self.__common_init__(config)

    def __common_init__(self, config):
        self.sshhost = config['sshhost']
        self.sshuser = config['sshuser']
        self.path = config['path']
        self.excludes = []
        if 'excludes' in config:
            self.excludes = config['excludes']

    def dump(self):
        tarfilename = '%s/%s.tar' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
        tarfile = open(tarfilename, 'wb')
        dumpargs = [
            'ssh', ('%s@%s' % (self.sshuser, self.sshhost)),
            'tar', 'cC', self.path
        ]
        for exclude in self.excludes:
            dumpargs.append('--exclude')
            dumpargs.append(exclude)
        dumpargs.append(".")
        logging.debug("Running '%s'" % (" ".join(dumpargs)))
        dumpproc1 = subprocess.Popen(dumpargs, stdout=tarfile, stderr=subprocess.PIPE)
        if dumpproc1.stdin:
            dumpproc1.stdin.close()
        dumpproc1.wait()
        exitcode = dumpproc1.returncode
        errmsg = dumpproc1.stderr.read()
        if errmsg != b'':
            logging.error(errmsg)
        if exitcode == 2:
            raise BackupException("Error while dumping: %s" % errmsg)
        tarfile.close()

        return [tarfilename, ]
