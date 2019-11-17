import os, os.path
import subprocess
import logging

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('mysql-ssh')
class MySQLSSH(BackupSource):
    def __init__(self, config):
        BackupSource.__init__(self, config, "MySQLSSH", "sql.gpg")
        self.__common_init__(config)

    def __common_init__(self, config):
        self.sshhost = config['sshhost']
        self.sshuser = config['sshuser']
        self.dbhost = config['dbhost']
        self.dbuser = config['dbuser']
        self.dbpass = config['dbpass']
        self.dbname = config['dbname']
        if 'noevents' in config:
            self.noevents = config['noevents']
        if 'options' in config:
            self.options = config['options']

    def dump(self):
        # Perform dump and remove creds file
        dumpfilename = '%s/%s.sql' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
        dumpfile = open(dumpfilename, 'wb')
        dumpargs = [
            'ssh', ('%s@%s' % (self.sshuser, self.sshhost)),
            'mysqldump', ('--host=%s' % self.dbhost), ('--user=%s' % self.dbuser), ('--pass=%s' % self.dbpass), '-R']
        if not 'noevents' in dir(self) or not self.noevents:
            dumpargs.append('--events')
        all_databases = False
        if hasattr(self, 'options'):
            for raw_option in self.options.split():
                option = raw_option.strip()
                dumpargs.append(option)
                if not all_databases and option == '--all-databases':
                    all_databases = True
        if not all_databases:
            dumpargs.append('--databases')
            for dbname in self.dbname.split():
                dumpargs.append(dbname)
        dumpproc1 = subprocess.Popen(dumpargs, stdout=dumpfile, stderr=subprocess.PIPE)
        if dumpproc1.stdin:
            dumpproc1.stdin.close()
        dumpproc1.wait()
        exitcode = dumpproc1.returncode
        errmsg = dumpproc1.stderr.read()
        if exitcode != 0:
            raise BackupException("Error while dumping: %s" % errmsg)
        dumpfile.close()

        return [dumpfilename, ]
