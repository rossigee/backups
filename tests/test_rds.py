import pytest
from unittest.mock import Mock, patch
from backups.sources.rds import RDS
from backups.sources.rdspostgresql import RDSPostgreSQL
from backups.exceptions import BackupException


class TestRDS:
    def test_init(self):
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

    def test_init_custom_instance_class(self):
        config = {
            'id': 'test-rds',
            'instancename': 'my-db',
            'region': 'us-east-1',
            'security_group': 'sg-12345',
            'instance_class': 'db.r5.large',
            'dbhost': 'localhost',
            'dbuser': 'user',
            'dbpass': 'pass',
            'dbname': 'mydb'
        }
        rds = RDS(config)
        assert rds.instance_class == 'db.r5.large'

    def test_init_with_credentials(self):
        config = {
            'id': 'test-rds',
            'instancename': 'my-db',
            'region': 'us-east-1',
            'security_group': 'sg-12345',
            'dbhost': 'localhost',
            'dbuser': 'user',
            'dbpass': 'pass',
            'dbname': 'mydb',
            'credentials': {
                'aws_access_key_id': 'AKID',
                'aws_secret_access_key': 'secret'
            }
        }
        rds = RDS(config)
        assert rds.credentials == True
        assert rds.aws_access_key == 'AKID'

    def test_wait_for_status_success(self):
        config = {
            'id': 'test-rds', 'instancename': 'my-db', 'region': 'us-east-1',
            'security_group': 'sg-12345', 'dbhost': 'localhost',
            'dbuser': 'user', 'dbpass': 'pass', 'dbname': 'mydb'
        }
        rds = RDS(config)
        mock_client = Mock()
        mock_client.describe_db_instances.return_value = {
            'DBInstances': [{'DBInstanceStatus': 'available', 'Endpoint': {'Address': 'host', 'Port': 3306}}]
        }
        result = rds._wait_for_status(mock_client, 'inst-id', 'available')
        assert result['DBInstanceStatus'] == 'available'

    def test_wait_for_status_failed_state(self):
        config = {
            'id': 'test-rds', 'instancename': 'my-db', 'region': 'us-east-1',
            'security_group': 'sg-12345', 'dbhost': 'localhost',
            'dbuser': 'user', 'dbpass': 'pass', 'dbname': 'mydb'
        }
        rds = RDS(config)
        mock_client = Mock()
        mock_client.describe_db_instances.return_value = {
            'DBInstances': [{'DBInstanceStatus': 'failed', 'Endpoint': {'Address': 'host', 'Port': 3306}}]
        }
        with pytest.raises(BackupException, match="unexpected status"):
            rds._wait_for_status(mock_client, 'inst-id', 'available')

    def test_no_snapshots_raises(self):
        config = {
            'id': 'test-rds', 'instancename': 'my-db', 'region': 'us-east-1',
            'security_group': 'sg-12345', 'dbhost': 'localhost',
            'dbuser': 'user', 'dbpass': 'pass', 'dbname': 'mydb'
        }
        rds = RDS(config)
        mock_client = Mock()
        mock_client.describe_db_snapshots.return_value = {'DBSnapshots': []}

        with patch.object(rds, '_get_client', return_value=mock_client):
            with pytest.raises(BackupException, match="No automated snapshots"):
                rds.dump()


class TestRDSPostgreSQL:
    def test_init(self):
        config = {
            'id': 'test-rds-pgsql',
            'instancename': 'my-pg-db',
            'region': 'us-east-1',
            'security_group': 'sg-12345',
            'dbhost': 'localhost',
            'dbuser': 'user',
            'dbpass': 'pass',
            'dbname': 'mydb'
        }
        rds = RDSPostgreSQL(config)
        assert rds.instancename == 'my-pg-db'
        assert rds.rds_region == 'us-east-1'
        assert rds.instance_class == 'db.t3.small'

    def test_init_with_credentials(self):
        config = {
            'id': 'test-rds-pgsql',
            'instancename': 'my-pg-db',
            'region': 'us-east-1',
            'security_group': 'sg-12345',
            'dbhost': 'localhost',
            'dbuser': 'user',
            'dbpass': 'pass',
            'dbname': 'mydb',
            'credentials': {
                'aws_access_key_id': 'AKID',
                'aws_secret_access_key': 'secret'
            }
        }
        rds = RDSPostgreSQL(config)
        assert rds.credentials == True

    def test_no_snapshots_raises(self):
        config = {
            'id': 'test-rds-pgsql', 'instancename': 'my-pg-db', 'region': 'us-east-1',
            'security_group': 'sg-12345', 'dbhost': 'localhost',
            'dbuser': 'user', 'dbpass': 'pass', 'dbname': 'mydb'
        }
        rds = RDSPostgreSQL(config)
        mock_client = Mock()
        mock_client.describe_db_snapshots.return_value = {'DBSnapshots': []}

        with patch.object(rds, '_get_client', return_value=mock_client):
            with pytest.raises(BackupException, match="No automated snapshots"):
                rds.dump()
