import backups.encrypt

import os, os.path
import subprocess
import logging

from backups.exceptions import BackupException

class MySQL:
    def __init__(self, backup_id, config):
        self.id = backup_id
        self.name = backup_id
        self.type = "MySQL"
        config_id = 'mysql-%s' % backup_id
        self.dbname = config.get(config_id, 'dbname')
        if config.has_option(config_id, 'defaults'):
            self.defaults = config.get(config_id, 'defaults')
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
        zipfilename = '%s/%s.sql.gz' % (self.tmpdir, self.id)
        logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
        zipfile = open(zipfilename, 'wb')
        if 'defaults' in dir(self):
            dumpargs = ['mysqldump', '--defaults-file=%s' % self.defaults]
        else:
            dumpargs = ['mysqldump', ]
        if not 'noevents' in dir(self) or not self.noevents:
            dumpargs.append('--events')
        dumpargs.append(self.dbname)
        dumpproc1 = subprocess.Popen(dumpargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dumpproc2 = subprocess.Popen(['gzip'], stdin=dumpproc1.stdout, stdout=zipfile)
        dumpproc1.stdout.close()
        dumpproc1.wait()
        exitcode = dumpproc1.returncode
        errmsg = dumpproc1.stderr.read()
        if exitcode != 0:
            raise BackupException("Error while dumping: %s" % errmsg)
        zipfile.close()
        return zipfilename
    
    def dump_and_compress(self):
        filename = self.dump()
        encfilename = backups.encrypt.encrypt(filename, self.passphrase)
        os.unlink(filename)
        return encfilename

