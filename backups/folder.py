import os, os.path
import subprocess
import logging

from backups.exceptions import BackupException
from backups.source import BackupSource

class Folder(BackupSource):
    def __init__(self, backup_id, config):
        self.id = backup_id
        self.name = backup_id
        self.type = "Folder"
        self.suffix = "tar.gpg"
        config_id = 'folder-%s' % backup_id
        self.path = config.get(config_id, 'path')
        if config.has_option(config_id, 'name'):
            self.name = config.get(config_id, 'name')
        if config.has_option(config_id, 'passphrase'):
            self.passphrase = config.get(config_id, 'passphrase')
        else:
            self.passphrase = config.get('defaults', 'passphrase')
        if config.has_option('defaults', 'tmpdir'):
            self.tmpdir = config.get('defaults', 'tmpdir')
        else:
            self.tmpdir = "/var/tmp"
        self.excludes = []
        for k, v in config.items(config_id):
            if k == 'exclude':
                self.excludes.append(v)

    def dump(self):
        zipfilename = '%s/%s.tar.gz' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
        zipfile = open(zipfilename, 'wb')
        os.chdir(os.path.dirname(self.path))
        dumpargs = ['sudo', 'tar', 'cfz', zipfilename, os.path.basename(self.path)]
        for exclude in self.excludes:
            dumpargs.append('--exclude')
            dumpargs.append(exclude)
        dumpproc1 = subprocess.Popen(dumpargs, stdout=zipfile, stderr=subprocess.PIPE)
        dumpproc1.wait()
        exitcode = dumpproc1.returncode
        errmsg = dumpproc1.stderr.read()
        if exitcode != 0:
            raise BackupException("Error while dumping: %s" % errmsg)
        zipfile.close()
        return zipfilename
