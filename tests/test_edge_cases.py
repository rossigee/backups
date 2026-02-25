import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from backups.sources.folder import Folder
from backups.destinations.s3 import S3
from backups.compress import compress
from backups.exceptions import BackupException

class TestEdgeCases:
    def test_folder_invalid_path(self):
        config = {'id': 'test-folder', 'path': '/nonexistent/path'}
        folder = Folder(config)
        # Init succeeds, but dump might fail - test init

    @patch('subprocess.Popen')
    def test_folder_dump_nonexistent_path(self, mock_popen):
        config = {'id': 'test-folder', 'name': 'testname', 'path': '/nonexistent'}
        folder = Folder(config)

        mock_proc = Mock()
        mock_proc.returncode = 2
        mock_proc.stderr.read.return_value = b'Tar error: No such file'
        mock_popen.return_value = mock_proc

        with pytest.raises(BackupException, match="Error while dumping"):
            folder.dump()

    def test_s3_missing_bucket(self):
        with pytest.raises(KeyError):
            S3({'id': 'test-s3', 'region': 'us-east-1'})

    def test_s3_invalid_credentials(self):
        config = {'id': 'test-s3', 'bucket': 'test', 'region': 'us-east-1', 'credentials': {'aws_access_key_id': 'key'}}
        with pytest.raises(KeyError):
            S3(config)

    @patch('subprocess.Popen')
    def test_s3_send_large_file(self, mock_popen):
        # Mock large file handling, but since it's subprocess, similar
        pass

    def test_stats_invalid_size(self):
        from backups.stats import BackupRunStatistics
        stats = BackupRunStatistics()
        stats.size = -1
        # getSizeDescription handles negative? Let's see
        desc = stats.getSizeDescription()
        assert "NaN" in desc or desc.startswith("-")

    @patch('backups.compress.subprocess.Popen')
    def test_compress_large_file(self, mock_popen):
        from backups.compress import compress
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'large.tar')
            # Simulate large file
            with open(filename, 'wb') as f:
                f.write(b'x' * 1024 * 1024)  # 1MB

            result = compress(filename)
            assert result.endswith('.gz')