import os
import pytest
import tempfile
from unittest.mock import Mock, patch

pytest.importorskip('dropbox')
from backups.destinations.dropbox import Dropbox
from backups.exceptions import BackupException


class TestDropbox:
    def test_init(self):
        config = {'id': 'test-dropbox', 'access_token': 'token123'}
        dest = Dropbox(config)
        assert dest.access_token == 'token123'
        assert dest.folder == '/backups'

    def test_init_custom_folder(self):
        config = {'id': 'test-dropbox', 'access_token': 'token123', 'folder': '/mybackups'}
        dest = Dropbox(config)
        assert dest.folder == '/mybackups'

    def test_init_with_retention(self):
        config = {'id': 'test-dropbox', 'access_token': 'token123', 'retention_copies': '7'}
        dest = Dropbox(config)
        assert dest.retention_copies == 7

    @patch('backups.destinations.dropbox.dropbox.Dropbox')
    def test_send_success(self, mock_dbx_class):
        config = {'id': 'test-dropbox', 'access_token': 'token123'}
        dest = Dropbox(config)
        mock_dbx = Mock()
        mock_dbx_class.return_value = mock_dbx

        with tempfile.NamedTemporaryFile(suffix='.tar.gpg', delete=False) as f:
            f.write(b'data')
            fname = f.name
        try:
            result = dest.send('sourceid', 'sourcename', fname)
            assert result.startswith('/backups/sourceid/')
            mock_dbx.files_upload.assert_called_once()
        finally:
            os.unlink(fname)

    @patch('backups.destinations.dropbox.dropbox.Dropbox')
    def test_send_failure(self, mock_dbx_class):
        import dropbox as dbxmod
        config = {'id': 'test-dropbox', 'access_token': 'token123'}
        dest = Dropbox(config)
        mock_dbx = Mock()
        mock_dbx.files_upload.side_effect = dbxmod.exceptions.ApiError(
            'req_id', 'error', 'user_msg_text', 'user_msg_locale')
        mock_dbx_class.return_value = mock_dbx

        with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as f:
            fname = f.name
        try:
            with pytest.raises(BackupException, match="Error while uploading"):
                dest.send('sourceid', 'sourcename', fname)
        finally:
            os.unlink(fname)
