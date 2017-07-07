import datetime

# Abstract
class BackupDestination:
    def __init__(self, config):
        self.runtime = datetime.datetime.now()

        self.hostname = config.get_or_envvar('defaults', 'hostname', 'BACKUPS_HOSTNAME')

        self.retention_copies = 0
        try:
            self.retention_copies = int(config.get('s3', 'retention_copies'))
        except:
            pass
        try:
            self.retention_copies = int(config.get_or_envvar('defaults', 'retention_copies', 'RETENTION_COPIES'))
        except:
            pass

        self.retention_days = 0
        try:
            self.retention_days = int(config.get('s3', 'retention_days'))
        except:
            pass
        try:
            self.retention_days = int(config.get_or_envvar('defaults', 'retention_days', 'RETENTION_DAYS'))
        except:
            pass
