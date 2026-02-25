import os, os.path
import datetime
import logging

import dropbox
from dropbox.exceptions import ApiError

from backups.exceptions import BackupException
from backups.destinations import backupdestination
from backups.destinations.destination import BackupDestination

@backupdestination('dropbox')
class Dropbox(BackupDestination):
    def __init__(self, config):
        BackupDestination.__init__(self, config)
        self.access_token = config['access_token']
        self.folder = config.get('folder', '/backups')

    def _get_client(self):
        return dropbox.Dropbox(self.access_token)

    def send(self, id, name, filename):
        remote_path = "%s/%s/%s/%s" % (
            self.folder.rstrip('/'),
            id,
            self.runtime.strftime("%Y%m%d%H%M%S"),
            os.path.basename(filename))
        logging.info("Uploading '%s' backup for '%s' to Dropbox (%s)..." % (name, self.id, remote_path))
        try:
            dbx = self._get_client()
            with open(filename, 'rb') as f:
                dbx.files_upload(f.read(), remote_path)
        except ApiError as e:
            raise BackupException("Error while uploading (%s): %s" % (self.id, str(e)))
        return remote_path

    def cleanup(self, id, name):
        folder_path = "%s/%s" % (self.folder.rstrip('/'), id)
        logging.info("Clearing down older '%s' backups for '%s' from Dropbox (%s)..." % (name, self.id, folder_path))
        try:
            dbx = self._get_client()
            result = dbx.files_list_folder(folder_path)
            entries = result.entries
            while result.has_more:
                result = dbx.files_list_folder_continue(result.cursor)
                entries.extend(result.entries)
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                return []
            raise BackupException("Error listing Dropbox folder (%s): %s" % (self.id, str(e)))

        candidates = []
        for entry in entries:
            if isinstance(entry, dropbox.files.FolderMetadata):
                candidates.append([entry.name, entry.path_lower])
        candidates.sort()

        removable = []
        retained = []
        if self.retention_copies > 0:
            paths = [p for n, p in candidates]
            if len(paths) > self.retention_copies:
                removable = paths[0:(len(paths) - self.retention_copies)]
            retained = paths[(len(paths) - self.retention_copies):]
        for path in removable:
            logging.info("Removing '%s'..." % path)
            try:
                dbx.files_delete_v2(path)
            except ApiError as e:
                logging.warning("Failed to remove '%s': %s" % (path, str(e)))

        return retained
