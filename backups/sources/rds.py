import os, os.path
import subprocess
import logging
import random
import time

import boto3

import backups.encrypt

from backups.sources import backupsource
from backups.exceptions import BackupException
from backups.sources.source import BackupSource
from backups.sources.mysql import MySQL

@backupsource('rds')
class RDS(MySQL):
    def __init__(self, config):
        BackupSource.__init__(self, config, "RDS", "sql.gpg")
        self.__common_init__(config)

    def __common_init__(self, config):
        MySQL.__common_init__(self, config)

        self.instancename = config['instancename']
        self.rds_region = config['region']
        self.security_group = config['security_group']
        self.instance_class = "db.m1.small"
        if 'instance_class' in config:
            self.instance_class = config['instance_class']
        # These are optional if using a .boto file, however, allow users to override.
        self.credentials = 'credentials' in config
        if self.credentials:
            self.aws_access_key = config['credentials']['aws_access_key_id']
            self.aws_secret_key = config['credentials']['aws_secret_access_key']

    def _connect_with_boto(self):
        kwargs = dict()
        if self.credentials:
            kwargs['aws_access_key_id'] = self.aws_access_key
            kwargs['aws_secret_access_key'] = self.aws_secret_key
        return boto3.client('rds', **kwargs)

    def dump(self):
        # Identify the most recent snapshot for the given instancename
        client = self._connect_with_boto()
        snapshots = client.get_all_dbsnapshots()
        suitable = []
        prefix = "DBSnapshot:rds:%s" % self.instancename
        for i in snapshots:
            if str(i)[:len(prefix)] == prefix:
                suitable.append(i)
        if len(suitable) < 1:
            raise Exception("No suitable snapshots found to work from.")
        suitable.sort()
        snapshot_id = suitable.pop().id
        logging.info("Chosen '%s' to restore..." % snapshot_id)

        # Restore a copy of the snapshot
        instance_id = "tmp-%s-%s" % (self.instancename, random.randint(10000, 99999))
        dbinstance = client.restore_dbinstance_from_dbsnapshot(snapshot_id, instance_id, self.instance_class)
        logging.info("Started RDS instance '%s'..." % instance_id)
        while dbinstance.status not in ('available', 'stopped'):
            logging.debug("Waiting for RDS instance (%s)..." % dbinstance.status)
            time.sleep(20)
            dbinstance.update()
        if dbinstance.status != 'available':
            raise Exception("Could not start RDS instance from snapshot.")
        (hostname, port) = dbinstance.endpoint
        logging.info("RDS instance is %s (%s)." % (dbinstance.status, hostname))

        # Set it with a security group that allows us to connect to it
        logging.debug("Setting security group to %s..." % self.security_group)
        sgroups = [self.security_group]
        dbinstance.modify(security_groups=sgroups, backup_retention_period=0, apply_immediately=True)
        dbinstance.update()
        while dbinstance.status not in ('available', 'stopped'):
            logging.debug("Waiting for RDS instance (%s)..." % dbinstance.status)
            time.sleep(20)
            dbinstance.update()

        # Wait for security group change to take effect (otherwise connect fails)
        for i in range(6):
            logging.debug("Waiting a couple of minutes for RDS instance to settle (%s)..." % dbinstance.status)
            time.sleep(20)
            dbinstance.update()

        # Fire off the mysqldump
        try:
            dumpfilename = MySQL.dump(self)[0]
        finally:
            # Clear down the temporary RDS instance
            logging.info("Terminating RDS instance...")
            dbinstance.stop(skip_final_snapshot=True)

        return [dumpfilename, ]
