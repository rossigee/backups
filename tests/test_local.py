import os
import pytest
import tempfile
from backups.destinations.local import Local


class TestLocal:
    def test_init(self):
        config = {'id': 'test-local', 'path': '/tmp/backups'}
        dest = Local(config)
        assert dest.path == '/tmp/backups'

    def test_init_with_retention(self):
        config = {'id': 'test-local', 'path': '/tmp/backups', 'retention_copies': '3', 'retention_days': '7'}
        dest = Local(config)
        assert dest.retention_copies == 3
        assert dest.retention_days == 7

    def test_send_success(self):
        with tempfile.TemporaryDirectory() as basedir:
            destdir = os.path.join(basedir, 'dest')
            config = {'id': 'test-local', 'path': destdir}
            dest = Local(config)

            srcfile = os.path.join(basedir, 'backup.tar.gpg')
            with open(srcfile, 'w') as f:
                f.write('data')

            result = dest.send('sourceid', 'sourcename', srcfile)
            assert os.path.exists(result)
            assert result.endswith('backup.tar.gpg')

    def test_send_creates_nested_dirs(self):
        with tempfile.TemporaryDirectory() as basedir:
            destdir = os.path.join(basedir, 'nonexistent', 'nested')
            config = {'id': 'test-local', 'path': destdir}
            dest = Local(config)

            srcfile = os.path.join(basedir, 'backup.tar')
            with open(srcfile, 'w') as f:
                f.write('data')

            result = dest.send('sourceid', 'sourcename', srcfile)
            assert os.path.exists(result)

    def test_cleanup_no_retention(self):
        with tempfile.TemporaryDirectory() as basedir:
            config = {'id': 'test-local', 'path': basedir}
            dest = Local(config)
            result = dest.cleanup('sourceid', 'sourcename')
            assert result == []

    def test_cleanup_with_retention_copies(self):
        with tempfile.TemporaryDirectory() as basedir:
            config = {'id': 'test-local', 'path': basedir, 'retention_copies': '1'}
            dest = Local(config)

            sourcedir = os.path.join(basedir, 'sourceid')
            os.makedirs(os.path.join(sourcedir, '20230101120000'))
            os.makedirs(os.path.join(sourcedir, '20230102120000'))

            retained = dest.cleanup('sourceid', 'sourcename')
            assert len(retained) == 1
            assert '20230102120000' in retained[0]
            assert not os.path.exists(os.path.join(sourcedir, '20230101120000'))

    def test_cleanup_nonexistent_dir(self):
        config = {'id': 'test-local', 'path': '/nonexistent/path'}
        dest = Local(config)
        result = dest.cleanup('sourceid', 'sourcename')
        assert result == []
