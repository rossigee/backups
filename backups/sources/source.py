import backups.encrypt

import os

# Abstract
class BackupSource:
    def __init__(self, backup_id, config, config_id, type, suffix):
        self.id = backup_id
        self.type = type
        self.suffix = suffix
        if config.has_option(config_id, 'name'):
            self.name = config.get(config_id, 'name')
        if config.has_option(config_id, 'passphrase'):
            self.passphrase = config.get(config_id, 'passphrase')
        else:
            self.passphrase = config.get_or_envvar('defaults', 'passphrase', 'BACKUPS_PASSPHRASE')
        if config.has_option('defaults', 'tmpdir'):
            self.tmpdir = config.get_or_envvar('defaults', 'tmpdir', 'BACKUPS_TMPDIR')
        else:
            self.tmpdir = "/var/tmp"

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
