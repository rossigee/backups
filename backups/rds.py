import os, os.path
import subprocess
import logging
import random
import time

import boto.rds

from backups.exceptions import BackupException
from backups.source import BackupSource

class RDS(BackupSource):
    def __init__(self, backup_id, config):
        self.id = backup_id
        self.name = backup_id
        self.type = "RDS"
        config_id = 'rds-%s' % backup_id
        self.dbname = config.get(config_id, 'dbname')
        self.instancename = config.get(config_id, 'instancename')
        if config.has_option(config_id, 'defaults'):
            self.defaults = config.get(config_id, 'defaults')
        if config.has_option(config_id, 'noevents'):
            self.noevents = config.get(config_id, 'noevents')
        if config.has_option(config_id, 'name'):
            self.name = config.get(config_id, 'name')
        if config.has_option(config_id, 'passphrase'):
            self.passphrase = config.get(config_id, 'passphrase')
        else:
            self.passphrase = config.get('defaults', 'passphrase')
        if config.has_option('defaults', 'tmpdir'):
            self.tmpdir = config.get('defaults', 'tmpdir')
        else:
            self.tmpdir = "/var/tmp"
        self.hostname = config.get('defaults', 'hostname')

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
            dumpfilename = '%s/%s.sql' % (self.tmpdir, self.id)
            logging.info("Backing up '%s' (%s)..." % (self.name, self.type))
            dumpfile = open(dumpfilename, 'wb')
            if 'defaults' in dir(self):
                dumpargs = ['mysqldump', ('--defaults-file=%s' % self.defaults), ('--host=%s' % hostname)]
            else:
                dumpargs = ['mysqldump', ('--host=%s' % hostname)]
            if not 'noevents' in dir(self) or not self.noevents:
                dumpargs.append('--events')
            dumpargs.append(self.dbname)
            dumpproc1 = subprocess.Popen(dumpargs, stdout=dumpfile, stderr=subprocess.PIPE)
            dumpproc1.stdout.close()
            dumpproc1.wait()
            exitcode = dumpproc1.returncode
            errmsg = dumpproc1.stderr.read()
            if exitcode != 0:
                raise BackupException("Error while dumping: %s" % errmsg)
            dumpfile.close()

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
