# Abstract
class BackupNotification:
    def __init__(self, config, section):
        self.notify_on_start = False
        if config.has_option(section, 'notify_on_start'):
            self.notify_on_start = config.get(section, 'notify_on_start') == 'True'
        self.notify_on_success = False
        if config.has_option(section, 'notify_on_success'):
            self.notify_on_success = config.get(section, 'notify_on_success') == 'True'
        self.notify_on_failure = True
        if config.has_option(section, 'notify_on_failure'):
            self.notify_on_failure = config.get(section, 'notify_on_failure') == 'True'

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
