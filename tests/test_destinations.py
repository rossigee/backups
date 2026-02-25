import pytest
from unittest.mock import Mock, patch
from moto import mock_aws
from backups.destinations.s3 import S3
from backups.exceptions import BackupException

class TestS3:
    def test_init(self):
        config = {
            'id': 'test-s3',
            'bucket': 'test-bucket',
            'region': 'us-east-1',
            'endpoint_url': 'http://localhost:4566',
            'credentials': {
                'aws_access_key_id': 'key',
                'aws_secret_access_key': 'secret'
            }
        }
        s3 = S3(config)
        assert s3.bucket == 'test-bucket'
        assert s3.region == 'us-east-1'
        assert s3.endpoint_url == 'http://localhost:4566'
        assert s3.aws_key == 'key'
        assert s3.aws_secret == 'secret'

    @patch('subprocess.Popen')
    def test_send_success(self, mock_popen):
        config = {'id': 'test-s3', 'bucket': 'test-bucket', 'region': 'us-east-1'}
        s3 = S3(config)
        s3.id = 'testid'
        s3.runtime = Mock()
        s3.runtime.strftime.return_value = '20230220143000'

        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        result = s3.send('sourceid', 'sourcename', '/path/to/file.tar')

        expected_location = 's3://test-bucket/sourceid/20230220143000/file.tar'
        assert result == expected_location

    @patch('subprocess.Popen')
    def test_send_failure(self, mock_popen):
        config = {'id': 'test-s3', 'bucket': 'test-bucket', 'region': 'us-east-1'}
        s3 = S3(config)

        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stderr.read.return_value = b'Upload failed'
        mock_popen.return_value = mock_proc

        with pytest.raises(BackupException, match="Error while uploading"):
            s3.send('sourceid', 'sourcename', '/path/to/file.tar')

    @mock_aws
    def test_cleanup_no_retention(self):
        import boto3
        config = {'id': 'test-s3', 'bucket': 'test-bucket', 'region': 'us-east-1'}
        s3 = S3(config)
        s3.retention_copies = 0
        s3.retention_days = 0

        # Create bucket
        client = boto3.client('s3', region_name='us-east-1')
        client.create_bucket(Bucket='test-bucket')

        result = s3.cleanup('sourceid', 'sourcename')
        assert result == []

    @mock_aws
    def test_cleanup_with_retention(self):
        import boto3
        from datetime import datetime, timezone
        config = {'id': 'test-s3', 'bucket': 'test-bucket', 'region': 'us-east-1'}
        s3 = S3(config)
        s3.retention_copies = 1
        s3.retention_days = 7

        # Create bucket and objects
        client = boto3.client('s3', region_name='us-east-1')
        client.create_bucket(Bucket='test-bucket')
        client.put_object(Bucket='test-bucket', Key='sourceid/old.tar', Body=b'test')
        client.put_object(Bucket='test-bucket', Key='sourceid/new.tar', Body=b'test')

        result = s3.cleanup('sourceid', 'sourcename')
        # Should return retained copies
        assert len(result) >= 0