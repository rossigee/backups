import os
import pytest
import tempfile
from unittest.mock import Mock, patch

pytest.importorskip('b2sdk')
from backups.destinations.b2 import B2
from backups.exceptions import BackupException


class TestB2:
    def test_init(self):
        config = {
            'id': 'test-b2',
            'bucket': 'my-bucket',
            'credentials': {
                'application_key_id': 'keyid123',
                'application_key': 'appkey456'
            }
        }
        dest = B2(config)
        assert dest.bucket_name == 'my-bucket'
        assert dest.application_key_id == 'keyid123'
        assert dest.application_key == 'appkey456'

    def test_init_with_retention(self):
        config = {
            'id': 'test-b2',
            'bucket': 'my-bucket',
            'retention_copies': '5',
            'retention_days': '30',
            'credentials': {'application_key_id': 'kid', 'application_key': 'key'}
        }
        dest = B2(config)
        assert dest.retention_copies == 5
        assert dest.retention_days == 30

    @patch('backups.destinations.b2.B2Api')
    @patch('backups.destinations.b2.InMemoryAccountInfo')
    def test_send_success(self, mock_info, mock_api_class):
        config = {
            'id': 'test-b2',
            'bucket': 'my-bucket',
            'credentials': {'application_key_id': 'kid', 'application_key': 'key'}
        }
        dest = B2(config)
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_bucket = Mock()
        mock_api.get_bucket_by_name.return_value = mock_bucket

        with tempfile.NamedTemporaryFile(suffix='.tar.gpg', delete=False) as f:
            f.write(b'data')
            fname = f.name
        try:
            result = dest.send('sourceid', 'sourcename', fname)
            assert result.startswith('b2://my-bucket/')
            mock_bucket.upload_local_file.assert_called_once()
        finally:
            os.unlink(fname)

    @patch('backups.destinations.b2.B2Api')
    @patch('backups.destinations.b2.InMemoryAccountInfo')
    def test_send_failure(self, mock_info, mock_api_class):
        config = {
            'id': 'test-b2',
            'bucket': 'my-bucket',
            'credentials': {'application_key_id': 'kid', 'application_key': 'key'}
        }
        dest = B2(config)
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        mock_bucket = Mock()
        mock_bucket.upload_local_file.side_effect = Exception("Upload failed")
        mock_api.get_bucket_by_name.return_value = mock_bucket

        with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as f:
            fname = f.name
        try:
            with pytest.raises(BackupException, match="Error while uploading"):
                dest.send('sourceid', 'sourcename', fname)
        finally:
            os.unlink(fname)
