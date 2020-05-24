import logging
import datetime

import elasticsearch

from backups.exceptions import BackupException
from backups.notifications import backupnotification
from backups.notifications.notification import BackupNotification

@backupnotification('elasticsearch')
class Elasticsearch(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'elasticsearch')
        self.url = config['url']
        self.username = None
        self.password = None
        if 'credentials' in config:
            self.username = config['credentials']['username']
            self.password = config['credentials']['password']
        self.indexpattern = config['indexpattern']
        self.notify_on_success = True
        self.notify_on_failure = True

    def _write(self, source, doc):
        if self.username is None:
            es = elasticsearch.Elasticsearch([self.url],
                verify_certs=False
            )
        else:
            es = elasticsearch.Elasticsearch([self.url],
                verify_certs=False,
                http_auth=(self.username,self.password)
            )

        try:
            # Ensure index exists (i.e. on period rollover)
            index = datetime.datetime.now().strftime(self.indexpattern)
            es.indices.create(index=index, ignore=400)

            # Write statistics document to index
            res = es.index(index=index, body=doc)
            logging.info("Wrote statistics for job '%s' to Elasticsearch." % source.id)
        except Exception as e:
            logging.error("Unable to write statistics for job '%s' to Elasticsearch: %s" % (source.id, str(e)))

    def notify_success(self, source, hostname, filename, stats):
        doc = {
            '@timestamp': datetime.datetime.now().isoformat(),
            'status': 'success',
            'source': {
                "id": source.id,
                "name": source.name
            },
            'hostname': hostname,
            'stats': {
                'starttime': None if stats.starttime is None else stats.starttime.isoformat(),
                'endtime': None if stats.endtime is None else stats.endtime.isoformat(),
                'size': stats.size,
                'dumptime': stats.dumptime,
                'dumpedfiles': stats.dumpedfiles,
                'uploadtime': stats.uploadtime,
                'retainedfiles': stats.retainedfiles
            }
        }
        self._write(source, doc)

    def notify_failure(self, source, hostname, e):
        doc = {
            'status': 'failed',
            'source': {
                "id": source.id,
                "name": source.name
            },
            'hostname': hostname,
            'error': str(e)
        }
        self._write(source, doc)
