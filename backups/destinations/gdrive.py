import os, os.path
import datetime
import logging
import contextlib

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

SCOPES = ['https://www.googleapis.com/auth/drive']

@backupdestination('gdrive')
class GDrive(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        self.creds_file = config['creds_file']
        self.folder_id = config['folder_id']

    def _get_tracer(self):
        if hasattr(self, 'tracer') and self.tracer is not None:
            return self.tracer
        class _NoOpTracer:
            @contextlib.contextmanager
            def start_as_current_span(self, name, **kwargs):
                class _NoOpSpan:
                    def set_attribute(self, *a, **k): pass
                    def record_exception(self, *a, **k): pass
                    def set_status(self, *a, **k): pass
                yield _NoOpSpan()
        return _NoOpTracer()

    def _get_service(self):
        credentials = service_account.Credentials.from_service_account_file(
            self.creds_file, scopes=SCOPES)
        return build('drive', 'v3', credentials=credentials)

    def _get_or_create_folder(self, service, parent_id, folder_name):
        query = "name='%s' and '%s' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false" % (folder_name, parent_id)
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        if files:
            return files[0]['id']
        metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = service.files().create(body=metadata, fields='id').execute()
        return folder['id']

    def send(self, id, name, filename):
        with self._get_tracer().start_as_current_span("gdrive_upload") as span:
            span.set_attribute("destination.id", self.id)
            span.set_attribute("gdrive.folder_id", self.folder_id)
            span.set_attribute("source.id", id)
            span.set_attribute("upload.file", filename)
            
            logging.info("Uploading '%s' backup for '%s' to Google Drive..." % (name, self.id))
            try:
                service = self._get_service()
                source_folder_id = self._get_or_create_folder(service, self.folder_id, id)
                ts_folder_id = self._get_or_create_folder(service, source_folder_id, self.runtime.strftime("%Y%m%d%H%M%S"))
                file_metadata = {
                    'name': os.path.basename(filename),
                    'parents': [ts_folder_id]
                }
                media = MediaFileUpload(filename, resumable=True)
                uploaded = service.files().create(
                    body=file_metadata, media_body=media, fields='id,name').execute()
                span.set_attribute("gdrive.file_id", uploaded.get('id'))
                span.set_attribute("gdrive.file_name", uploaded.get('name'))
            except HttpError as e:
                span.record_exception(BackupException("Error while uploading (%s): %s" % (self.id, str(e))))
                raise BackupException("Error while uploading (%s): %s" % (self.id, str(e)))
            return "gdrive://%s/%s" % (self.folder_id, uploaded.get('name'))

    def cleanup(self, id, name):
        with self._get_tracer().start_as_current_span("gdrive_cleanup") as span:
            span.set_attribute("destination.id", self.id)
            span.set_attribute("gdrive.folder_id", self.folder_id)
            span.set_attribute("source.id", id)
            span.set_attribute("retention.copies", self.retention_copies)
            span.set_attribute("retention.days", self.retention_days)
            
            logging.info("Clearing down older '%s' backups for '%s' from Google Drive..." % (name, self.id))
            try:
                service = self._get_service()
                query = "name='%s' and '%s' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false" % (id, self.folder_id)
                results = service.files().list(q=query, fields="files(id)").execute()
                source_folders = results.get('files', [])
                if not source_folders:
                    span.set_attribute("source_folder.count", 0)
                    return []
                source_folder_id = source_folders[0]['id']

                query = "'%s' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false" % source_folder_id
                results = service.files().list(q=query, fields="files(id,name,createdTime)", orderBy="createdTime").execute()
                candidates = [(f['createdTime'], f['id'], f['name']) for f in results.get('files', [])]
                candidates.sort()
                span.set_attribute("object.count", len(candidates))
            except HttpError as e:
                span.record_exception(BackupException("Error listing Google Drive folder (%s): %s" % (self.id, str(e))))
                raise BackupException("Error listing Google Drive folder (%s): %s" % (self.id, str(e)))

            removable = []
            retained = []
            if self.retention_copies > 0:
                items = candidates
                if len(items) > self.retention_copies:
                    removable = items[0:(len(items) - self.retention_copies)]
                retained = [n for d, fid, n in items[(len(items) - self.retention_copies):]]
            if self.retention_days > 0:
                now = datetime.datetime.now(datetime.timezone.utc)
                for created, fid, fname in candidates:
                    from dateutil import parser as dtparser
                    age = (now - dtparser.parse(created)).days
                    if age > self.retention_days:
                        removable.append((created, fid, fname))
            for created, fid, fname in removable:
                logging.info("Removing '%s'..." % fname)
                try:
                    service.files().delete(fileId=fid).execute()
                except HttpError as e:
                    logging.warning("Failed to remove '%s': %s" % (fname, str(e)))
            span.set_attribute("removed.count", len(removable))
            span.set_attribute("retained.count", len(retained))

            return retained
