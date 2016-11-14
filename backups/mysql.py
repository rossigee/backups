import os, os.path
import subprocess
import logging

from backups.exceptions import BackupException
from backups.source import BackupSource

class MySQL(BackupSource):
    def __init__(self, backup_id, config):
        self.id = backup_id
        self.name = backup_id
        self.type = "MySQL"
        self.suffix = "sql.gpg"
        config_id = 'mysql-%s' % backup_id
        self.dbhost = config.get(config_id, 'dbhost')
        self.dbname = config.get(config_id, 'dbname')
        self.dbuser = config.get(config_id, 'dbuser')
        self.dbpass = config.get(config_id, 'dbpass')
        if config.has_option(config_id, 'noevents'):
            self.noevents = config.get(config_id, 'noevents')
        self.dbname = config.get(config_id, 'dbname')
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
        self.hostname = config.get('defaults', 'hostname')

    def dump(self):
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

        dumpfilename = '%s/%s.sql' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
        dumpfile = open(dumpfilename, 'wb')
        if 'mysql_host' in dir(self):
            dumpargs = ['mysqldump', '--defaults-file=%s' % credsfilename]
        else:
            dumpargs = ['mysqldump', ]
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

        os.unlink(credsfilename)

        return dumpfilename
