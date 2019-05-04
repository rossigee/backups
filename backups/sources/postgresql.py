import os, os.path
import subprocess
import logging

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('pgsql')
class PostgreSQL(BackupSource):
    def __init__(self, config):
        BackupSource.__init__(self, config, "PostgreSQL", "sql.gpg")
        self.__common_init__(config)

    def __common_init__(self, config):
        self.dbhost = config['dbhost']
        self.dbuser = config['dbuser']
        self.dbpass = config['dbpass']
        self.dbname = config['dbname']
        if 'defaults' in config:
            self.defaults = config['defaults']

    def dump(self):
        # Create temporary credentials file
        credsfilename = '%s/%s.pgpass' % (self.tmpdir, self.id)
        with open(credsfilename, 'w') as credsfile:
            credsfile.write(
                "%s:%s:%s:%s:%s\n" % \
                (self.dbhost, '5432', self.dbname, self.dbuser, self.dbpass)
            )
            credsfile.flush()
            credsfile.close()

        # Perform dump and remove creds file
        try:
            dumpfilename = '%s/%s.sql' % (self.tmpdir, self.id)
            logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
            dumpfile = open(dumpfilename, 'wb')
            dumpargs = ['pg_dump', '-h', self.dbhost, '--username', self.dbuser, self.dbname]
            dumpenv = os.environ.copy()
            dumpenv['PGPASSFILE'] = credsfilename
            dumpproc1 = subprocess.Popen(dumpargs, stdout=dumpfile, stderr=subprocess.PIPE, env=dumpenv)
            if dumpproc1.stdout:
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
