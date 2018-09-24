import os
import time

import backups.encrypt


# Abstract
class BackupSource:
    def __init__(self, config, type, suffix):
        self.id = config['id']
        self.type = type
        self.suffix = suffix
        self.tmpdir = "/var/tmp"
        if 'name' in config:
            self.name = config['name']
        if 'passphrase' in config:
            self.passphrase = config['passphrase']
        if 'tmpdir' in config:
            self.tmpdir = config['tmpdir']

    def dump_and_compress(self, stats):
        d_starttime = time.time()
        filenames = self.dump()
        d_endtime = time.time()
        stats.dumptime_dump = d_endtime - d_starttime
        if isinstance(filenames, basestring):
            filenames = [filenames, ]
        encrypted_files = []

        e_starttime = time.time()
        for filename in filenames:
            encfilename = backups.encrypt.encrypt(filename, self.passphrase)
            encrypted_files.append(encfilename)
            os.unlink(filename)
        e_endtime = time.time()
        stats.dumptime_encrypt = e_endtime - e_starttime
        return encrypted_files
