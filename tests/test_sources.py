import json
import os
import sys
import tempfile
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from backups.sources.folder import Folder
from backups.sources.mysql import MySQL
from backups.sources.mysqlssh import MySQLSSH
from backups.sources.postgresql import PostgreSQL
from backups.sources.folderssh import FolderSSH
from backups.sources.lvmssh import LVMLogicalVolume, dev_mapper_name
from backups.sources.snapshot import Snapshot
from backups.exceptions import BackupException

# Azure SDK is optional; inject stubs before importing the module
for _dep in ['adal', 'msrestazure', 'msrestazure.azure_active_directory',
             'msrestazure.azure_cloud', 'azure', 'azure.mgmt', 'azure.mgmt.compute']:
    sys.modules.setdefault(_dep, MagicMock())
from backups.sources.azure_managed_disk import AzureManagedDisk

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


class TestMySQL:
    def _config(self):
        return {
            'id': 'test-mysql',
            'dbhost': 'db.example.com',
            'dbuser': 'root',
            'dbpass': 'secret',
            'dbname': 'mydb',
        }

    def test_init(self):
        mysql = MySQL(self._config())
        assert mysql.dbhost == 'db.example.com'
        assert mysql.dbuser == 'root'
        assert mysql.dbpass == 'secret'
        assert mysql.dbname == 'mydb'
        assert mysql.type == 'MySQL'

    def test_init_with_options(self):
        config = dict(self._config())
        config['noevents'] = True
        config['options'] = '--single-transaction'
        mysql = MySQL(config)
        assert mysql.noevents == True
        assert mysql.options == '--single-transaction'

    @patch('os.unlink')
    @patch('os.chmod')
    @patch('subprocess.Popen')
    def test_dump_success(self, mock_popen, mock_chmod, mock_unlink):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        mysql = MySQL(self._config())
        mysql.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            result = mysql.dump()

        assert result == ['/var/tmp/test-mysql.sql']
        args, _ = mock_popen.call_args
        assert 'mysqldump' in args[0]
        assert '--databases' in args[0]
        assert 'mydb' in args[0]
        mock_unlink.assert_called_once()

    @patch('os.unlink')
    @patch('os.chmod')
    @patch('subprocess.Popen')
    def test_dump_error(self, mock_popen, mock_chmod, mock_unlink):
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stderr.read.return_value = b'Access denied'
        mock_popen.return_value = mock_proc

        mysql = MySQL(self._config())
        mysql.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            with pytest.raises(BackupException, match='Error while dumping'):
                mysql.dump()

        mock_unlink.assert_called_once()

    @patch('os.unlink')
    @patch('subprocess.Popen')
    def test_dump_with_defaults_file(self, mock_popen, mock_unlink):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        config = dict(self._config())
        config['defaults'] = '/etc/mysql/backup.cnf'
        mysql = MySQL(config)
        mysql.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            result = mysql.dump()

        assert result == ['/var/tmp/test-mysql.sql']
        args, _ = mock_popen.call_args
        assert '--defaults-file=/etc/mysql/backup.cnf' in args[0]
        mock_unlink.assert_called_once_with('/etc/mysql/backup.cnf')

    @patch('os.unlink')
    @patch('os.chmod')
    @patch('subprocess.Popen')
    def test_dump_all_databases(self, mock_popen, mock_chmod, mock_unlink):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        config = dict(self._config())
        config['options'] = '--all-databases'
        mysql = MySQL(config)
        mysql.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            mysql.dump()

        args, _ = mock_popen.call_args
        assert '--all-databases' in args[0]
        assert '--databases' not in args[0]


class TestPostgreSQL:
    def _config(self):
        return {
            'id': 'test-pg',
            'dbhost': 'pg.example.com',
            'dbuser': 'postgres',
            'dbpass': 'secret',
            'dbname': 'mydb',
        }

    def test_init(self):
        pg = PostgreSQL(self._config())
        assert pg.dbhost == 'pg.example.com'
        assert pg.dbuser == 'postgres'
        assert pg.dbpass == 'secret'
        assert pg.dbname == 'mydb'
        assert pg.type == 'PostgreSQL'

    @patch('os.unlink')
    @patch('subprocess.Popen')
    def test_dump_success(self, mock_popen, mock_unlink):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        pg = PostgreSQL(self._config())
        pg.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            result = pg.dump()

        assert result == ['/var/tmp/test-pg.sql']
        args, kwargs = mock_popen.call_args
        assert 'pg_dump' in args[0]
        assert 'pg.example.com' in args[0]
        assert 'mydb' in args[0]
        assert kwargs['env']['PGPASSFILE'] == '/var/tmp/test-pg.pgpass'
        mock_unlink.assert_called_once()

    @patch('os.unlink')
    @patch('subprocess.Popen')
    def test_dump_error(self, mock_popen, mock_unlink):
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stderr.read.return_value = b'could not connect'
        mock_popen.return_value = mock_proc

        pg = PostgreSQL(self._config())
        pg.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            with pytest.raises(BackupException, match='Error while dumping'):
                pg.dump()

        mock_unlink.assert_called_once()


class TestMySQLSSH:
    def _config(self):
        return {
            'id': 'test-mysqlssh',
            'sshhost': 'remote.example.com',
            'sshuser': 'backupuser',
            'dbhost': '127.0.0.1',
            'dbuser': 'root',
            'dbpass': 'secret',
            'dbname': 'mydb',
        }

    def test_init(self):
        m = MySQLSSH(self._config())
        assert m.sshhost == 'remote.example.com'
        assert m.sshuser == 'backupuser'
        assert m.dbhost == '127.0.0.1'
        assert m.dbname == 'mydb'
        assert m.type == 'MySQLSSH'

    def test_init_with_options(self):
        config = dict(self._config())
        config['noevents'] = True
        config['options'] = '--single-transaction'
        m = MySQLSSH(config)
        assert m.noevents == True
        assert m.options == '--single-transaction'

    @patch('subprocess.Popen')
    def test_dump_success(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        m = MySQLSSH(self._config())
        m.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            result = m.dump()

        assert result == ['/var/tmp/test-mysqlssh.sql']
        args, _ = mock_popen.call_args
        assert 'ssh' in args[0]
        assert 'backupuser@remote.example.com' in args[0]
        assert 'mysqldump' in args[0]
        assert '--databases' in args[0]

    @patch('subprocess.Popen')
    def test_dump_error(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 2
        mock_proc.stderr.read.return_value = b'Connection refused'
        mock_popen.return_value = mock_proc

        m = MySQLSSH(self._config())
        m.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            with pytest.raises(BackupException, match='Error while dumping'):
                m.dump()

    @patch('subprocess.Popen')
    def test_dump_exitcode_1_is_allowed(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stderr.read.return_value = b'warning only'
        mock_popen.return_value = mock_proc

        m = MySQLSSH(self._config())
        m.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            result = m.dump()

        assert result == ['/var/tmp/test-mysqlssh.sql']

    @patch('subprocess.Popen')
    def test_dump_all_databases(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        config = dict(self._config())
        config['options'] = '--all-databases'
        m = MySQLSSH(config)
        m.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            m.dump()

        args, _ = mock_popen.call_args
        assert '--all-databases' in args[0]
        assert '--databases' not in args[0]


class TestFolderSSH:
    def _config(self):
        return {
            'id': 'test-folderssh',
            'sshhost': 'remote.example.com',
            'sshuser': 'backupuser',
            'path': '/var/data',
        }

    def test_init(self):
        f = FolderSSH(self._config())
        assert f.sshhost == 'remote.example.com'
        assert f.sshuser == 'backupuser'
        assert f.path == '/var/data'
        assert f.excludes == []
        assert f.type == 'FolderSSH'

    def test_init_with_excludes(self):
        config = dict(self._config())
        config['excludes'] = ['*.tmp', 'cache/']
        f = FolderSSH(config)
        assert f.excludes == ['*.tmp', 'cache/']

    @patch('subprocess.Popen')
    def test_dump_success(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        f = FolderSSH(self._config())
        f.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            result = f.dump()

        assert result == ['/var/tmp/test-folderssh.tar']
        args, _ = mock_popen.call_args
        assert 'ssh' in args[0]
        assert 'backupuser@remote.example.com' in args[0]
        assert 'tar' in args[0]

    @patch('subprocess.Popen')
    def test_dump_with_excludes(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr.read.return_value = b''
        mock_popen.return_value = mock_proc

        config = dict(self._config())
        config['excludes'] = ['*.tmp', 'cache/']
        f = FolderSSH(config)
        f.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            f.dump()

        args, _ = mock_popen.call_args
        assert '--exclude' in args[0]
        assert '*.tmp' in args[0]
        assert 'cache/' in args[0]

    @patch('subprocess.Popen')
    def test_dump_error(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 2
        mock_proc.stderr.read.return_value = b'ssh: connect to host'
        mock_popen.return_value = mock_proc

        f = FolderSSH(self._config())
        f.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            with pytest.raises(BackupException, match='Error while dumping'):
                f.dump()

    @patch('subprocess.Popen')
    def test_dump_exitcode_1_is_allowed(self, mock_popen):
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stderr.read.return_value = b'file changed as we read it'
        mock_popen.return_value = mock_proc

        f = FolderSSH(self._config())
        f.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            result = f.dump()

        assert result == ['/var/tmp/test-folderssh.tar']


class TestLVMLogicalVolume:
    def _config(self):
        return {
            'id': 'test-lvm',
            'sshhost': 'remote.example.com',
            'sshuser': 'root',
            'vg_name': 'vg0',
            'lv_name': 'data',
            'size': '1G',
            'retain_snapshots': 2,
        }

    def test_dev_mapper_name(self):
        assert dev_mapper_name('vg0', 'data') == '/dev/mapper/vg0-data'

    def test_dev_mapper_name_escapes_hyphens(self):
        assert dev_mapper_name('vg-0', 'data-lv') == '/dev/mapper/vg--0-data--lv'

    def test_init(self):
        lvm = LVMLogicalVolume(self._config())
        assert lvm.sshhost == 'remote.example.com'
        assert lvm.sshuser == 'root'
        assert lvm.vg_name == 'vg0'
        assert lvm.lv_name == 'data'
        assert lvm.size == '1G'
        assert lvm.retain_snapshots == 2

    @patch('subprocess.Popen')
    def test_dump_success(self, mock_popen):
        lvs_json = json.dumps({
            'report': [{'lv': [{'lv_name': 'data-20240101120000'}]}]
        }).encode()

        proc_create = Mock()
        proc_create.returncode = 0
        proc_create.stdout.read.return_value = b''
        proc_create.stderr.read.return_value = b''

        proc_list = Mock()
        proc_list.returncode = 0
        proc_list.stdout.read.return_value = lvs_json
        proc_list.stderr.read.return_value = b''

        proc_dd = Mock()
        proc_dd.returncode = 0
        proc_dd.stderr.read.return_value = b''

        mock_popen.side_effect = [proc_create, proc_list, proc_dd]

        lvm = LVMLogicalVolume(self._config())
        lvm.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            result = lvm.dump()

        assert result == ['/var/tmp/data.dump']
        assert mock_popen.call_count == 3

        first_args, _ = mock_popen.call_args_list[0]
        assert 'lvcreate' in first_args[0]
        assert 'ssh' in first_args[0]

        second_args, _ = mock_popen.call_args_list[1]
        assert 'lvs' in second_args[0]

        third_args, _ = mock_popen.call_args_list[2]
        assert 'dd' in third_args[0]

    @patch('subprocess.Popen')
    def test_dump_removes_redundant_snapshots(self, mock_popen):
        lvs_json = json.dumps({
            'report': [{'lv': [
                {'lv_name': 'data-20240101120000'},
                {'lv_name': 'data-20240102120000'},
            ]}]
        }).encode()

        proc_create = Mock()
        proc_create.returncode = 0
        proc_create.stdout.read.return_value = b''
        proc_create.stderr.read.return_value = b''

        proc_list = Mock()
        proc_list.returncode = 0
        proc_list.stdout.read.return_value = lvs_json
        proc_list.stderr.read.return_value = b''

        proc_remove = Mock()
        proc_remove.returncode = 0
        proc_remove.stderr.read.return_value = b''

        proc_dd = Mock()
        proc_dd.returncode = 0
        proc_dd.stderr.read.return_value = b''

        mock_popen.side_effect = [proc_create, proc_list, proc_remove, proc_dd]

        config = dict(self._config())
        config['retain_snapshots'] = 1
        lvm = LVMLogicalVolume(config)
        lvm.tmpdir = '/var/tmp'

        with patch('builtins.open', mock_open()):
            lvm.dump()

        assert mock_popen.call_count == 4
        remove_args, _ = mock_popen.call_args_list[2]
        assert 'lvremove' in remove_args[0]

    @patch('subprocess.Popen')
    def test_dump_snapshot_error(self, mock_popen):
        proc_create = Mock()
        proc_create.returncode = 2
        proc_create.stdout.read.return_value = b''
        proc_create.stderr.read.return_value = b'lvcreate failed'
        mock_popen.return_value = proc_create

        lvm = LVMLogicalVolume(self._config())
        lvm.tmpdir = '/var/tmp'

        with pytest.raises(BackupException, match='Error while snapshotting'):
            lvm.dump()


class TestSnapshot:
    def _config(self):
        return {
            'id': 'test-snap',
            'volume_id': 'vol-0abc123',
            'availability_zone': 'eu-west-1a',
            'credentials': {
                'aws_access_key_id': 'AKIAIOSFODNN7EXAMPLE',
                'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
            },
        }

    def test_init(self):
        snap = Snapshot(self._config())
        assert snap.vol == 'vol-0abc123'
        assert snap.az == 'eu-west-1a'
        assert snap.aws_access_key == 'AKIAIOSFODNN7EXAMPLE'
        assert snap.credentials is not None

    @patch('boto3.client')
    def test_connect_with_boto_uses_credentials(self, mock_boto_client):
        snap = Snapshot(self._config())
        snap._connect_with_boto('ec2')
        mock_boto_client.assert_called_once()
        _, kwargs = mock_boto_client.call_args
        assert kwargs['aws_access_key_id'] == 'AKIAIOSFODNN7EXAMPLE'

    def test_dump_writes_status_file(self):
        snap = Snapshot(self._config())
        snap.tmpdir = '/var/tmp'
        snap.snapshot = Mock(return_value='snap-0abc123')

        with patch('builtins.open', mock_open()) as m:
            result = snap.dump()

        assert result == ['/var/tmp/test-snap.status']
        handle = m()
        written = b''.join(c.args[0] for c in handle.write.call_args_list)
        data = json.loads(written.decode())
        assert data['status'] == 'OK'
        assert data['retval'] == 'snap-0abc123'


class TestAzureManagedDisk:
    def _config(self):
        return {
            'id': 'test-azure',
            'subscription_id': 'sub-123',
            'source_resource_group': 'rg-source',
            'destination_resource_group': 'rg-dest',
            'disk_name': 'datadisk',
            'retain_snapshots': 3,
        }

    def test_init(self):
        disk = AzureManagedDisk(self._config())
        assert disk.subscription_id == 'sub-123'
        assert disk.source_resource_group == 'rg-source'
        assert disk.destination_resource_group == 'rg-dest'
        assert disk.disk_name == 'datadisk'
        assert disk.retain_snapshots == 3
        assert disk.type == 'AzureManagedDisk'