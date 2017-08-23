import os, os.path
import subprocess
import logging

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('mysql')
class MySQL(BackupSource):
    def __init__(self, config):
        BackupSource.__init__(self, config, "MySQL", "sql.gpg")
        self.__common_init__(config)

    def __common_init__(self, config):
        self.dbhost = config['dbhost']
        self.dbuser = config['dbuser']
        self.dbpass = config['dbpass']
        self.dbname = config['dbname']
        if 'defaults' in config:
            self.defaults = config['defaults']
        if 'noevents' in config:
            self.noevents = config['noevents']

    def dump(self):
        # Create temporary credentials file
        if 'defaults' in dir(self):
            credsfilename = self.defaults
        elif self.dbuser is not None:
            credsfilename = '%s/%s.my.cnf' % (self.tmpdir, self.id)
            credsfile = open(credsfilename, 'wb')
            credsfile.write(
                "[client]\n" \
                "host=%s\n" \
                "user=%s\n" \
                "password=%s\n\n" % \
                (self.dbhost, self.dbuser, self.dbpass)
            )
            credsfile.flush()
            credsfile.close()
            os.chmod(credsfilename, 0400)

        # Perform dump and remove creds file
        try:
            dumpfilename = '%s/%s.sql' % (self.tmpdir, self.id)
            logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
            dumpfile = open(dumpfilename, 'wb')
            dumpargs = ['mysqldump', ('--defaults-file=%s' % credsfilename), ('--host=%s' % self.dbhost), '-R']
            if not 'noevents' in dir(self) or not self.noevents:
                dumpargs.append('--events')
            dumpargs.append(self.dbname)
            dumpproc1 = subprocess.Popen(dumpargs, stdout=dumpfile, stderr=subprocess.PIPE)
            if  dumpproc1.stdout:
                dumpproc1.stdout.close()
            dumpproc1.wait()
            exitcode = dumpproc1.returncode
            errmsg = dumpproc1.stderr.read()
            if exitcode != 0:
                raise BackupException("Error while dumping: %s" % errmsg)
            dumpfile.close()
        finally:
            os.unlink(credsfilename)

        return [dumpfilename, ]
