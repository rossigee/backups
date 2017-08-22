import backups.encrypt

import os

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

    def dump_and_compress(self):
        filenames = self.dump()
        if isinstance(filenames, basestring):
            filenames = [filenames, ]
        encrypted_files = []
        for filename in filenames:
            encfilename = backups.encrypt.encrypt(filename, self.passphrase)
            encrypted_files.append(encfilename)
            os.unlink(filename)
        return encrypted_files
