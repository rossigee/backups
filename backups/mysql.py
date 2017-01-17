import os, os.path
import subprocess
import logging

from backups.exceptions import BackupException
from backups.source import BackupSource

class MySQL(BackupSource):
    def __init__(self, backup_id, config):
        config_id = 'mysql-%s' % backup_id
        BackupSource.__init__(self, backup_id, config, config_id, "MySQL", "sql.gpg")
        self.__common_init__(backup_id, config, config_id)

    def __common_init__(self, backup_id, config, config_id):
        try:
            self.dbhost = config.get(config_id, 'dbhost')
        except:
            self.dbhost = config.get_or_envvar(config_id, 'dbhost', 'MYSQL_HOST')
        try:
            self.dbuser = config.get(config_id, 'dbuser')
        except:
            self.dbuser = config.get_or_envvar(config_id, 'dbuser', 'MYSQL_USER')
        try:
            self.dbpass = config.get(config_id, 'dbpass')
        except:
            self.dbpass = config.get_or_envvar(config_id, 'dbpass', 'MYSQL_PASS')
        self.dbname = config.get(config_id, 'dbname')
        if config.has_option(config_id, 'defaults'):
            self.defaults = config.get(config_id, 'defaults')
        if config.has_option(config_id, 'noevents'):
            self.noevents = config.get(config_id, 'noevents')
        self.hostname = config.get_or_envvar('defaults', 'hostname', 'BACKUPS_HOSTNAME')

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
                "pass=%s\n\n" % \
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
            dumpargs = ['mysqldump', ('--defaults-file=%s' % credsfilename), ('--host=%s' % self.dbhost)]
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

        return dumpfilename
