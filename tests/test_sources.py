import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from backups.sources.folder import Folder
from backups.exceptions import BackupException

class TestFolder:
    def test_init(self):
        config = {'id': 'test-folder', 'path': '/tmp/test', 'excludes': ['*.log']}
        folder = Folder(config)
        assert folder.path == '/tmp/test'
        assert folder.excludes == ['*.log']
        assert folder.type == 'Folder'

    def test_init_no_excludes(self):
        config = {'id': 'test-folder', 'path': '/tmp/test'}
        folder = Folder(config)
        assert folder.excludes == []

    @patch('subprocess.Popen')
    @patch('os.chdir')
    def test_dump_success(self, mock_chdir, mock_popen):
        config = {'id': 'test-folder', 'path': '/tmp/test'}
        folder = Folder(config)
        folder.tmpdir = '/tmp'
        folder.id = 'testid'
        folder.name = 'testname'

        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        with patch('builtins.open', mock_open()):
            result = folder.dump()

        assert result == ['/tmp/testid.tar']
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert 'sudo' in args[0]
        assert 'tar' in args[0]

    @patch('subprocess.Popen')
    @patch('os.chdir')
    def test_dump_error(self, mock_chdir, mock_popen):
        config = {'id': 'test-folder', 'name': 'testname', 'path': '/tmp/test'}
        folder = Folder(config)

        mock_proc = Mock()
        mock_proc.returncode = 2
        mock_proc.stderr.read.return_value = b'Tar error'
        mock_popen.return_value = mock_proc

        with patch('builtins.open', mock_open()):
            with pytest.raises(BackupException, match="Error while dumping"):
                folder.dump()