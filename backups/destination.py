# Abstract
class BackupDestination:
    def __init__(self, config):
        self.hostname = config.get_or_envvar('defaults', 'hostname', 'BACKUPS_HOSTNAME')

        try:
            self.retention_copies = int(config.get('s3', 'retention_copies'))
        except:
            try:
                self.retention_copies = int(config.get('default', 'retention_copies', 'RETENTION_COPIES'))
            except:
                self.retention_copies = 0

        try:
            self.retention_days = int(config.get('s3', 'retention_days'))
        except:
            try:
                self.retention_days = int(config.get('default', 'retention_days', 'RETENTION_DAYS'))
            except:
                self.retention_days = 0
