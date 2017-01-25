import os, os.path
import subprocess
import logging

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('folder')
class Folder(BackupSource):
    def __init__(self, backup_id, config):
        config_id = 'folder-%s' % backup_id
        BackupSource.__init__(self, backup_id, config, config_id, "Folder", "tar.gpg")
        self.path = config.get(config_id, 'path')
        self.excludes = []
        for k, v in config.items(config_id):
            if k == 'exclude':
                self.excludes.append(v)

    def dump(self):
        tarfilename = '%s/%s.tar' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
        tarfile = open(tarfilename, 'wb')
        os.chdir(os.path.dirname(self.path))
        dumpargs = ['sudo', 'tar', 'cf', tarfilename, os.path.basename(self.path)]
        for exclude in self.excludes:
            dumpargs.append('--exclude')
            dumpargs.append(exclude)
        dumpproc1 = subprocess.Popen(dumpargs, stdout=tarfile, stderr=subprocess.PIPE)
        dumpproc1.wait()
        exitcode = dumpproc1.returncode
        errmsg = dumpproc1.stderr.read()
        if exitcode != 0:
            raise BackupException("Error while dumping: %s" % errmsg)
        tarfile.close()
        return tarfilename
