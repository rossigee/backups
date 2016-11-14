import urllib, urllib2
import os, os.path
import json
import logging

from backups.notification import BackupNotification

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

class Prometheus(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'prometheus')
        self.url = config.get('prometheus', 'url')
        self.notify_on_success = True
        self.notify_on_failure = False

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

        push_to_gateway(self.url, job=source.id, registry=registry)

        logging.info("Pushed metrics for job '%s' to gateway (%s)" % (source.id, self.url))
