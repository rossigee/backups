import os, os.path
import json
import logging
import base64

import requests

from prometheus_client import CollectorRegistry, Gauge, Summary, generate_latest, CONTENT_TYPE_LATEST

from backups.exceptions import BackupException
from backups.notifications import backupnotification
from backups.notifications.notification import BackupNotification

@backupnotification('prometheus')
class Prometheus(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'prometheus')
        self.url = config['url']
        self.username = None
        self.password = None
        self.api_key = None
        if 'credentials' in config:
            self.username = config['credentials']['username']
            self.password = config['credentials']['password']
        if 'api_key' in config:
            self.api_key = config['api_key']
        self.notify_on_success = True
        self.notify_on_failure = False

    def _get_headers(self):
        headers = {'Content-Type': CONTENT_TYPE_LATEST}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        elif self.username is not None and self.password is not None:
            auth_value = f'{self.username}:{self.password}'.encode()
            auth_token = base64.b64encode(auth_value).decode()
            headers['Authorization'] = f'Basic {auth_token}'
        return headers

    def notify_success(self, source, hostname, filename, stats):
        registry = CollectorRegistry()

        s = Summary('backup_size', 'Size of backup file in bytes', registry=registry)
        s.observe(stats.size)
        s = Summary('backup_dumptime', 'Time taken to dump and compress/encrypt backup in seconds', registry=registry)
        s.observe(stats.dumptime)
        s = Summary('backup_uploadtime', 'Time taken to upload backup in seconds', registry=registry)
        s.observe(stats.uploadtime)
        g = Gauge('backup_retained_copies', 'Number of retained backups found on destination', registry=registry)
        g.set(len(stats.retained_copies))
        g = Gauge('backup_timestamp', 'Time backup completed as seconds-since-the-epoch', registry=registry)
        g.set_to_current_time()

        try:
            data = generate_latest(registry)
            url = '%s/metrics/job/%s' % (self.url.rstrip('/'), source.id)
            resp = requests.put(url, data=data, headers=self._get_headers())
            resp.raise_for_status()
            logging.info("Pushed metrics for job '%s' to gateway (%s)" % (source.id, self.url))
        except Exception as e:
            logging.error("Unable to push metrics for job '%s' to gateway (%s): %s" % (source.id, self.url, str(e)))
