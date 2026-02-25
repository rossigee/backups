import os
import pytest
import tempfile
from unittest.mock import Mock, patch

pytest.importorskip('minio')
from backups.destinations.minio import MinioDestination
from backups.exceptions import BackupException


class TestMinio:
    def test_init(self):
        config = {
            'id': 'test-minio',
            'bucket': 'my-bucket',
            'endpoint': 'play.min.io',
            'credentials': {'access_key': 'key', 'secret_key': 'secret'}
        }
        dest = MinioDestination(config)
        assert dest.bucket == 'my-bucket'
        assert dest.endpoint == 'play.min.io'
        assert dest.access_key == 'key'
        assert dest.secret_key == 'secret'
        assert dest.secure == True

    def test_init_insecure(self):
        config = {
            'id': 'test-minio',
            'bucket': 'my-bucket',
            'endpoint': 'localhost:9000',
            'secure': False,
            'credentials': {'access_key': 'key', 'secret_key': 'secret'}
        }
        dest = MinioDestination(config)
        assert dest.secure == False

    def test_init_with_retention(self):
        config = {
            'id': 'test-minio',
            'bucket': 'my-bucket',
            'endpoint': 'play.min.io',
            'retention_copies': '3',
            'credentials': {'access_key': 'key', 'secret_key': 'secret'}
        }
        dest = MinioDestination(config)
        assert dest.retention_copies == 3

    @patch('backups.destinations.minio.Minio')
    def test_send_success(self, mock_minio_class):
        config = {
            'id': 'test-minio',
            'bucket': 'my-bucket',
            'endpoint': 'play.min.io',
            'credentials': {'access_key': 'key', 'secret_key': 'secret'}
        }
        dest = MinioDestination(config)
        mock_client = Mock()
        mock_minio_class.return_value = mock_client

        with tempfile.NamedTemporaryFile(suffix='.tar.gpg', delete=False) as f:
            f.write(b'data')
            fname = f.name
        try:
            result = dest.send('sourceid', 'sourcename', fname)
            assert 'my-bucket' in result
            mock_client.fput_object.assert_called_once()
        finally:
            os.unlink(fname)

    @patch('backups.destinations.minio.Minio')
    def test_send_failure(self, mock_minio_class):
        from minio.error import S3Error
        config = {
            'id': 'test-minio',
            'bucket': 'my-bucket',
            'endpoint': 'play.min.io',
            'credentials': {'access_key': 'key', 'secret_key': 'secret'}
        }
        dest = MinioDestination(config)
        mock_client = Mock()
        mock_client.fput_object.side_effect = S3Error('NoSuchBucket', 'Bucket not found', None, None, None, None)
        mock_minio_class.return_value = mock_client

        with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as f:
            fname = f.name
        try:
            with pytest.raises(BackupException, match="Error while uploading"):
                dest.send('sourceid', 'sourcename', fname)
        finally:
            os.unlink(fname)
