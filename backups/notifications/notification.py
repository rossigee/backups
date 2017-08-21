# Abstract
class BackupNotification:
    def __init__(self, config, section):
        self.notify_on_start = False
        if 'notify_on_start' in config:
            self.notify_on_start = bool(config['notify_on_start'])
        self.notify_on_success = False
        if 'notify_on_success' in config:
            self.notify_on_success = bool(config['notify_on_success'])
        self.notify_on_failure = False
        if 'notify_on_failure' in config:
            self.notify_on_failure = bool(config['notify_on_failure'])

    def _notify_start(self, source, hostname):
        if not self.notify_on_start:
            return
        return self.notify_start(source, hostname)

    def _notify_success(self, source, hostname, filename, stats):
        if not self.notify_on_success:
            return
        return self.notify_success(source, hostname, filename, stats)

    def _notify_failure(self, source, hostname, e):
        if not self.notify_on_failure:
            return
        return self.notify_failure(source, hostname, e)
