import logging
import random
import time

import boto3

from backups.sources import backupsource
from backups.exceptions import BackupException
from backups.sources.source import BackupSource
from backups.sources.postgresql import PostgreSQL
from backups.sources.rds import RDS

@backupsource('rds-pgsql')
class RDSPostgreSQL(PostgreSQL):
    def __init__(self, config, type="RDS-PostgreSQL"):
        BackupSource.__init__(self, config, type, "sql.gpg")
        self.__common_init__(config)

    def __common_init__(self, config):
        PostgreSQL.__common_init__(self, config)
        self.instancename = config['instancename']
        self.rds_region = config['region']
        self.security_group = config['security_group']
        self.instance_class = config.get('instance_class', 'db.t3.small')
        self.credentials = 'credentials' in config
        if self.credentials:
            self.aws_access_key = config['credentials']['aws_access_key_id']
            self.aws_secret_key = config['credentials']['aws_secret_access_key']

    # Reuse RDS boto3 helpers
    _get_client = RDS._get_client
    _wait_for_status = RDS._wait_for_status

    def dump(self):
        client = self._get_client()

        # Find most recent automated snapshot for the instance
        response = client.describe_db_snapshots(
            DBInstanceIdentifier=self.instancename,
            SnapshotType='automated'
        )
        snapshots = response['DBSnapshots']
        if not snapshots:
            raise BackupException("No automated snapshots found for RDS instance '%s'" % self.instancename)
        snapshots.sort(key=lambda s: s['SnapshotCreateTime'])
        snapshot_id = snapshots[-1]['DBSnapshotIdentifier']
        logging.info("Chosen snapshot '%s' to restore..." % snapshot_id)

        # Restore snapshot to a temporary instance
        instance_id = "tmp-%s-%d" % (self.instancename[:20], random.randint(10000, 99999))
        client.restore_db_instance_from_db_snapshot(
            DBInstanceIdentifier=instance_id,
            DBSnapshotIdentifier=snapshot_id,
            DBInstanceClass=self.instance_class,
            MultiAZ=False,
            PubliclyAccessible=False
        )
        logging.info("Started restore of RDS instance '%s'..." % instance_id)

        try:
            instance = self._wait_for_status(client, instance_id, 'available')
            self.dbhost = instance['Endpoint']['Address']
            logging.info("RDS instance is available at %s" % self.dbhost)

            # Apply security group to allow connection
            client.modify_db_instance(
                DBInstanceIdentifier=instance_id,
                VpcSecurityGroupIds=[self.security_group],
                BackupRetentionPeriod=0,
                ApplyImmediately=True
            )
            self._wait_for_status(client, instance_id, 'available')

            logging.debug("Waiting for security group change to take effect...")
            time.sleep(30)

            dumpfilename = PostgreSQL.dump(self)[0]
        finally:
            logging.info("Deleting temporary RDS instance '%s'..." % instance_id)
            try:
                client.delete_db_instance(
                    DBInstanceIdentifier=instance_id,
                    SkipFinalSnapshot=True
                )
            except Exception as e:
                logging.warning("Failed to delete temporary RDS instance '%s': %s" % (instance_id, str(e)))

        return [dumpfilename]
