import urllib, urllib2
import os, os.path
import json
import logging
import base64

from backups.notification import BackupNotification

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.handlers.basic_auth import handler as http_basic_auth_handler

class Prometheus(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'prometheus')
        try:
            self.url = config.get('prometheus', 'url')
        except:
            self.url = config.get_or_envvar('defaults', 'url', 'PUSHGW_URL')
        try:
            self.username = config.get('prometheus', 'username')
        except:
            self.username = config.get_or_envvar('defaults', 'username', 'PUSHGW_USERNAME')
        try:
            self.password = config.get('prometheus', 'password')
        except:
            self.password = config.get_or_envvar('defaults', 'password', 'PUSHGW_PASSWORD')
        self.notify_on_success = True
        self.notify_on_failure = False

        auth_args = None
        if self.username is not None:
            self.auth_args = {
                'username': self.username,
                'password': self.password
            }

    def notify_success(self, source, hostname, filename, stats):
        registry = CollectorRegistry()

        g = Gauge('backup_size', 'Size of backup file in bytes', registry=registry)
        g.set(stats.size)
        g = Gauge('backup_dumptime', 'Time taken to dump and compress/encrypt backup in seconds', registry=registry)
        g.set(stats.dumptime)
        g = Gauge('backup_uploadtime', 'Time taken to upload backup in seconds', registry=registry)
        g.set(stats.uploadtime)
        g = Gauge('backup_retained_copies', 'Number of retained backups found on destination', registry=registry)
        g.set(stats.retained_copies)
        g = Gauge('backup_timestamp', 'Time backup completed as seconds-since-the-epoch', registry=registry)
        g.set_to_current_time()

        push_to_gateway(self.url, job=source.id, registry=registry, handler=http_basic_auth_handler, handler_args=self.auth_args)

        logging.info("Pushed metrics for job '%s' to gateway (%s)" % (source.id, self.url))
