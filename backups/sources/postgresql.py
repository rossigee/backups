import os, os.path
import subprocess
import logging

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('pgsql')
class PostgreSQL(BackupSource):
    def __init__(self, backup_id, config):
        config_id = 'pgsql-%s' % backup_id
        BackupSource.__init__(self, backup_id, config, config_id, "PostgreSQL", "sql.gpg")
        self.__common_init__(backup_id, config, config_id)

    def __common_init__(self, backup_id, config, config_id):
        try:
            self.dbhost = config.get(config_id, 'dbhost')
        except:
            self.dbhost = config.get_or_envvar(config_id, 'dbhost', 'PGSQL_HOST')
        try:
            self.dbuser = config.get(config_id, 'dbuser')
        except:
            self.dbuser = config.get_or_envvar(config_id, 'dbuser', 'PGSQL_USER')
        try:
            self.dbpass = config.get(config_id, 'dbpass')
        except:
            self.dbpass = config.get_or_envvar(config_id, 'dbpass', 'PGSQL_PASS')
        self.dbname = config.get(config_id, 'dbname')
        if config.has_option(config_id, 'defaults'):
            self.defaults = config.get(config_id, 'defaults')
        self.hostname = config.get_or_envvar('defaults', 'hostname', 'BACKUPS_HOSTNAME')

    def dump(self):
        # Create temporary credentials file
        credsfilename = '%s/%s.pgpass' % (self.tmpdir, self.id)
        credsfile = open(credsfilename, 'wb')
        credsfile.write(
            "%s:%s:%s:%s:%s\n" % \
            (self.dbhost, '5432', self.dbname, self.dbuser, self.dbpass)
        )
        credsfile.flush()
        credsfile.close()
        os.chmod(credsfilename, 0400)
        os.environ['PGPASSFILE'] = credsfilename

        # Perform dump and remove creds file
        try:
            dumpfilename = '%s/%s.sql' % (self.tmpdir, self.id)
            logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
            dumpfile = open(dumpfilename, 'wb')
            dumpargs = ['pg_dump', '-h', self.dbhost]
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
