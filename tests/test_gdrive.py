import os
import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock

pytest.importorskip('googleapiclient')
from backups.destinations.gdrive import GDrive
from backups.exceptions import BackupException


class TestGDrive:
    def test_init(self):
        config = {
            'id': 'test-gdrive',
            'creds_file': '/path/to/creds.json',
            'folder_id': 'folder123'
        }
        dest = GDrive(config)
        assert dest.creds_file == '/path/to/creds.json'
        assert dest.folder_id == 'folder123'

    def test_init_with_retention(self):
        config = {
            'id': 'test-gdrive',
            'creds_file': '/path/to/creds.json',
            'folder_id': 'folder123',
            'retention_copies': '10'
        }
        dest = GDrive(config)
        assert dest.retention_copies == 10

    @patch('backups.destinations.gdrive.MediaFileUpload')
    @patch('backups.destinations.gdrive.build')
    @patch('backups.destinations.gdrive.service_account.Credentials.from_service_account_file')
    def test_send_success(self, mock_creds, mock_build, mock_media):
        config = {
            'id': 'test-gdrive',
            'creds_file': '/path/to/creds.json',
            'folder_id': 'root_folder_id'
        }
        dest = GDrive(config)

        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.files().list().execute.return_value = {'files': [{'id': 'subfolder_id'}]}
        mock_service.files().create().execute.return_value = {'id': 'file_id', 'name': 'backup.tar.gpg'}

        with tempfile.NamedTemporaryFile(suffix='.tar.gpg', delete=False) as f:
            f.write(b'data')
            fname = f.name
        try:
            result = dest.send('sourceid', 'sourcename', fname)
            assert 'gdrive://' in result
        finally:
            os.unlink(fname)


class TestRDS:
    def test_init(self):
        from backups.sources.rds import RDS
        config = {
            'id': 'test-rds',
            'instancename': 'my-db',
            'region': 'us-east-1',
            'security_group': 'sg-12345',
            'dbhost': 'localhost',
            'dbuser': 'user',
            'dbpass': 'pass',
            'dbname': 'mydb'
        }
        rds = RDS(config)
        assert rds.instancename == 'my-db'
        assert rds.rds_region == 'us-east-1'
        assert rds.instance_class == 'db.t3.small'
