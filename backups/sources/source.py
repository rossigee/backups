import os
import time
import contextlib

import backups.compress
import backups.encrypt


# Abstract
class BackupSource:
    def __init__(self, config, type, suffix):
        self.id = config['id']
        self.type = type
        self.suffix = suffix
        self.tmpdir = "/var/tmp"
        self.recipients = []
        self.passphrase = ""
        self.name = config.get('name', self.id)
        if 'recipients' in config:
            self.recipients = config['recipients']
        if 'passphrase' in config:
            self.passphrase = config['passphrase']
        if 'tmpdir' in config:
            self.tmpdir = config['tmpdir']
        self.compress = False
        if 'compress_only' in config:
            self.compress = config['compress_only'] == 1
        self.tracer = None

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

    def dump_and_compress(self, stats):
        d_starttime = time.time()
        with self._get_tracer().start_as_current_span("source_dump") as dump_span:
            dump_span.set_attribute("source.id", self.id)
            dump_span.set_attribute("source.type", self.type)
            filenames = self.dump()
        d_endtime = time.time()
        stats.dumptime_dump = d_endtime - d_starttime
        if isinstance(filenames, str):
            filenames = [filenames, ]
        compressed_files = []

        e_starttime = time.time()
        self.encrypted = False
        self.gpg_recipients = None
        for filename in filenames:
            with self._get_tracer().start_as_current_span("compress_or_encrypt") as ce_span:
                ce_span.set_attribute("source.id", self.id)
                ce_span.set_attribute("input.file", filename)
                if self.compress:
                    compressed_filename = backups.compress.compress(filename)
                    self.encrypted = False
                    ce_span.set_attribute("operation", "compress")
                elif len(self.recipients) > 0:
                    compressed_filename = backups.encrypt.encrypt(filename, recipients=self.recipients)
                    os.unlink(filename)
                    self.encrypted = True
                    self.gpg_recipients = self.recipients
                    ce_span.set_attribute("operation", "encrypt_recipients")
                    ce_span.set_attribute("gpg.recipients", ','.join(self.recipients))
                else:
                    compressed_filename = backups.encrypt.encrypt(filename, passphrase=self.passphrase)
                    os.unlink(filename)
                    self.encrypted = True
                    ce_span.set_attribute("operation", "encrypt_passphrase")
                ce_span.set_attribute("output.file", compressed_filename)
            compressed_files.append(compressed_filename)
        e_endtime = time.time()
        stats.dumptime_encrypt = e_endtime - e_starttime
        return compressed_files
