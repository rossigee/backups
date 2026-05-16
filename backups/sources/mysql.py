import os, os.path
import subprocess
import logging
import contextlib

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('mysql')
class MySQL(BackupSource):
    def __init__(self, config, type="MySQL"):
        BackupSource.__init__(self, config, type, "sql.gpg")
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
        if 'options' in config:
            self.options = config['options']

    def _get_tracer(self):
        if hasattr(self, 'tracer') and self.tracer is not None:
            return self.tracer
        class _NoOpTracer:
            @contextlib.contextmanager
            def start_as_current_span(self, name, **kwargs):
                class _NoOpSpan:
                    def set_attribute(self, *a, **k): pass
                    def record_exception(self, *a, **k): pass
                    def set_status(self, *a, **k): pass
                yield _NoOpSpan()
        return _NoOpTracer()

    def dump(self):
        with self._get_tracer().start_as_current_span("mysql_dump") as dump_span:
            dump_span.set_attribute("source.id", self.id)
            dump_span.set_attribute("db.host", self.dbhost)
            dump_span.set_attribute("db.user", self.dbuser)
            dump_span.set_attribute("db.name", self.dbname)
            
            # Create temporary credentials file
            if 'defaults' in dir(self):
                credsfilename = self.defaults
            elif self.dbuser is not None:
                credsfilename = '%s/%s.my.cnf' % (self.tmpdir, self.id)
                credsfile = open(credsfilename, 'w')
                credsfile.write(
                    "[client]\n" \
                    "host=%s\n" \
                    "user=%s\n" \
                    "password=%s\n\n" % \
                    (self.dbhost, self.dbuser, self.dbpass)
                )
                credsfile.flush()
                credsfile.close()
                os.chmod(credsfilename, 0o400)

            # Perform dump and remove creds file
            try:
                dumpfilename = '%s/%s.sql' % (self.tmpdir, self.id)
                logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
                dumpfile = open(dumpfilename, 'wb')
                dumpargs = ['mysqldump', ('--defaults-file=%s' % credsfilename), ('--host=%s' % self.dbhost), '-R']
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
                    dump_span.record_exception(BackupException("Error while dumping: %s" % errmsg))
                    raise BackupException("Error while dumping: %s" % errmsg)
                dumpfile.close()
                dump_span.set_attribute("dump.file", dumpfilename)
            finally:
                os.unlink(credsfilename)

            return [dumpfilename, ]
