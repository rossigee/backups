import os
import time

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

    def dump_and_compress(self, stats):
        d_starttime = time.time()
        filenames = self.dump()
        d_endtime = time.time()
        stats.dumptime_dump = d_endtime - d_starttime
        if isinstance(filenames, str):
            filenames = [filenames, ]
        compressed_files = []

        e_starttime = time.time()
        for filename in filenames:
            if self.compress:
                compressed_filename = backups.compress.compress(filename)
            elif len(self.recipients) > 0:
                compressed_filename = backups.encrypt.encrypt(filename, recipients=self.recipients)
                os.unlink(filename)
            else:
                compressed_filename = backups.encrypt.encrypt(filename, passphrase=self.passphrase)
                os.unlink(filename)
            compressed_files.append(compressed_filename)
        e_endtime = time.time()
        stats.dumptime_encrypt = e_endtime - e_starttime
        return compressed_files
