import os, os.path
import subprocess
import logging
import random
import time

import boto.rds

from backups.exceptions import BackupException
from backups.sources.mysql import MySQL

class RDS(MySQL):
    def __init__(self, backup_id, config):
        config_id = 'rds-%s' % backup_id
        BackupSource.__init__(self, backup_id, config, config_id, "RDS", "sql.gpg")
        self.__common_init__(backup_id, config, config_id)

        self.instancename = config.get(config_id, 'instancename')
        self.rds_region = config.get(config_id, 'region')
        self.security_group = config.get(config_id, 'security_group')
        if config.has_option(config_id, 'instance_class'):
            self.instance_class = config.get(config_id, 'instance_class')
        else:
            self.instance_class = "db.m1.small"

    def dump(self):
        # Identify the most recent snapshot for the given instancename
        conn = boto.rds.connect_to_region(self.rds_region)
        snapshots = conn.get_all_dbsnapshots()
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
        dbinstance = conn.restore_dbinstance_from_dbsnapshot(snapshot_id, instance_id, self.instance_class)
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
            dumpfilename = MySQL.dump(self)
        finally:
            # Clear down the temporary RDS instance
            logging.info("Terminating RDS instance...")
            dbinstance.stop(skip_final_snapshot=True)

        return dumpfilename

    def dump_and_compress(self):
        filename = self.dump()
        encfilename = backups.encrypt.encrypt(filename, self.passphrase)
        os.unlink(filename)
        return encfilename
