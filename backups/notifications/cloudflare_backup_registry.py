import uuid
import json
import requests
import logging
import datetime

from backups.notifications.notification import BackupNotification
from backups.notifications import backupnotification


@backupnotification('cloudflare-backup-registry')
class CloudflareBackupRegistry(BackupNotification):
    def __init__(self, config):
        BackupNotification.__init__(self, config, 'cloudflare-backup-registry')
        self.url = config['url']
        self.token = config.get('token')
        self.metadata = config.get('metadata', {})

    def _send(self, payload):
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        try:
            r = requests.post(self.url, json=payload, headers=headers)
            r.raise_for_status()
            logging.info("Sent backup run notification to Cloudflare Backup Registry.")
        except requests.exceptions.HTTPError as err:
            logging.error(f"Unable to send notification to Cloudflare Backup Registry: {err}")

    def notify_success(self, source, hostname, filename, stats):
        payload = {
            "run_id": str(uuid.uuid4()),
            "job_name": source.name,
            "agent_id": hostname,
            "start_time": stats.start_time.isoformat() if hasattr(stats, 'start_time') else None,
            "end_time": stats.end_time.isoformat() if hasattr(stats, 'end_time') else None,
            "status": "success",
            "bytes_backed_up": getattr(stats, 'size', 0),
            "encrypted": getattr(source, 'encrypted', False),
            "encryption_status": "encrypted" if getattr(source, 'encrypted', False) else "unencrypted",
            "metadata": self.metadata
        }
        if payload['start_time'] and payload['end_time']:
            self._send(payload)
        else:
            logging.warning("Missing start_time or end_time for success notification")

    def notify_failure(self, source, hostname, e):
        end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        start_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=1)).isoformat()
        payload = {
            "run_id": str(uuid.uuid4()),
            "job_name": source.name,
            "agent_id": hostname,
            "start_time": start_time,
            "end_time": end_time,
            "status": "failure",
            "error": str(e),
            "metadata": self.metadata
        }
        self._send(payload)