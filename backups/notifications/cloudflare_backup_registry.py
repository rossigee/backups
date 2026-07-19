import uuid
import json
import requests
import logging
import datetime

from backups.notifications.notification import BackupNotification
from backups.notifications import backupnotification

try:
    from opentelemetry.trace import get_current_span
    from opentelemetry.context import get_current
    _otel_available = True
except ImportError:
    _otel_available = False


@backupnotification('cloudflare-backup-registry')
class CloudflareBackupRegistry(BackupNotification):
    def __init__(self, config):
        config.setdefault('notify_on_success', True)
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
        now = datetime.datetime.now(datetime.timezone.utc)
        start_time = stats.starttime.isoformat() if hasattr(stats, 'starttime') and stats.starttime else now.isoformat()
        end_time = stats.endtime.isoformat() if hasattr(stats, 'endtime') and stats.endtime else now.isoformat()

        gpg_recipients = getattr(source, 'gpg_recipients', None)
        encrypted = bool(gpg_recipients)
        
        backup_url = None
        if filename:
            if filename.startswith('https://') or filename.startswith('http://'):
                backup_url = filename
            elif '/' in filename and not filename.startswith('http'):
                parts = filename.split('/', 1)
                if len(parts) == 2:
                    endpoint = parts[0]
                    rest = parts[1]
                    if endpoint.startswith('backups.golder.lan'):
                        backup_url = f"https://{rest}"
        
        metadata = dict(self.metadata)
        if _otel_available:
            current_span = get_current_span(get_current())
            if current_span:
                span_context = current_span.get_span_context()
                metadata['trace_id'] = format(span_context.trace_id, '032x')

        if gpg_recipients:
            metadata['gpg_recipients'] = gpg_recipients
        
        payload = {
            "run_id": str(uuid.uuid4()),
            "job_name": source.name,
            "agent_id": hostname,
            "start_time": start_time,
            "end_time": end_time,
            "status": "success",
            "bytes_backed_up": getattr(stats, 'size', 0),
            "encrypted": encrypted,
            "encryption_status": "encrypted" if encrypted else "unencrypted",
            "backup_url": backup_url,
            "metadata": metadata
        }
        self._send(payload)

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