import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from backups.compress import compress
from backups.encrypt import encrypt
from backups.stats import BackupRunStatistics
from backups.exceptions import BackupException

class TestCompress:
    @patch('subprocess.Popen')
    def test_compress_success(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            result = compress(filename)
            expected = filename + '.gz'
            assert result == expected

    @patch('subprocess.Popen')
    def test_compress_failure(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            with pytest.raises(BackupException, match="Error while compressing"):
                compress(filename)

class TestEncrypt:
    @patch('subprocess.Popen')
    def test_encrypt_passphrase(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            result = encrypt(filename, passphrase='testpass')
            expected = filename + '.gpg'
            assert result == expected

    @patch('subprocess.Popen')
    def test_encrypt_recipients(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            result = encrypt(filename, recipients=['user@example.com'])
            expected = filename + '.gpg'
            assert result == expected

    def test_encrypt_no_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'test.tar')
            with open(filename, 'w') as f:
                f.write('test')

            with pytest.raises(BackupException, match="Misconfigured encryption"):
                encrypt(filename)

class TestBackupRunStatistics:
    def test_init(self):
        stats = BackupRunStatistics()
        assert stats.starttime is None
        assert stats.endtime is None
        assert stats.size is None
        assert stats.dumpedfiles == []
        assert stats.dumptime is None
        assert stats.uploadtime is None
        assert stats.retained_copies == []

    @pytest.mark.parametrize("size,expected", [
        (100, "100.0 bytes"),
        (1024, "1.0 KB"),
        (1024*1024, "1.0 MB"),
        (1024*1024*1024, "1.0 GB"),
        (1024*1024*1024*1024, "1.0 TB"),
    ])
    def test_getSizeDescription(self, size, expected):
        stats = BackupRunStatistics()
        stats.size = size
        assert stats.getSizeDescription() == expected