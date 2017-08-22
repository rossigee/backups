import datetime

# Abstract
class BackupDestination:
    def __init__(self, config):
        self.runtime = datetime.datetime.now()

        self.retention_copies = 0
        if 'retention_copies' in config:
            self.retention_copies = int(config['retention_copies'])
        self.retention_days = 0
        if 'retention_days' in config:
            self.retention_days = int(config['retention_days'])
