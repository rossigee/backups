import os, os.path
import subprocess
import logging
import contextlib

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('folder')
class Folder(BackupSource):
    def __init__(self, config, type="Folder"):
        BackupSource.__init__(self, config, type, "tar.gpg")
        self.path = config['path']
        self.excludes = []
        if 'excludes' in config:
            self.excludes = config['excludes']

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
        with self._get_tracer().start_as_current_span("folder_dump") as dump_span:
            dump_span.set_attribute("source.id", self.id)
            dump_span.set_attribute("source.path", self.path)
            dump_span.set_attribute("exclude.count", len(self.excludes))
            
            tarfilename = '%s/%s.tar' % (self.tmpdir, self.id)
            logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
            tarfile = open(tarfilename, 'wb')
            os.chdir(os.path.dirname(self.path))
            dumpargs = ['sudo', 'tar', 'cf', tarfilename, "./" + os.path.basename(self.path)]
            for exclude in self.excludes:
                dumpargs.append('--exclude')
                dumpargs.append(exclude)
            dumpproc1 = subprocess.Popen(dumpargs, stdout=tarfile, stderr=subprocess.PIPE)
            dumpproc1.wait()
            exitcode = dumpproc1.returncode
            errmsg = dumpproc1.stderr.read()
            if exitcode == 2:
                dump_span.record_exception(BackupException("Error while dumping: %s" % errmsg))
                raise BackupException("Error while dumping: %s" % errmsg)
            tarfile.close()
            dump_span.set_attribute("dump.file", tarfilename)
            return [tarfilename, ]
