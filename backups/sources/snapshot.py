import os, os.path
import subprocess
import boto.rds
import boto.ec2
import logging
import datetime
import json

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('snapshot')
class Snapshot(BackupSource):
    def __init__(self, backup_id, config):
        config_id = 'snapshot-%s' % backup_id
        BackupSource.__init__(self, backup_id, config, config_id, "Snapshot", None)
        self.vol = config.get(config_id, 'volume_id')
        self.datestr = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        try:
            self.az = config.get(config_id, 'availability_zone')
        except:
            self.az = config.get_or_envvar('defaults', 'availability_zone', 'AWS_AVAILABILITY_ZONE')
        try:
            self.aws_key = config.get(config_id, 'aws_access_key_id')
        except:
            self.aws_key = config.get_or_envvar('defaults', 'aws_access_key_id', 'AWS_ACCESS_KEY_ID')
        try:
            self.aws_secret = config.get('s3', 'aws_secret_access_key')
        except:
            self.aws_secret = config.get_or_envvar('defaults', 'aws_secret_access_key', 'AWS_SECRET_ACCESS_KEY')

    def dump(self):
        retval = self.snapshot()
        statfilename = '%s/%s.status' % (self.tmpdir, self.id)
        statfile = open(statfilename, 'wb')
        statfile.write(json.dumps({
            'status': "OK",
            'retval': str(retval)
        }))
        statfile.close()
        return statfilename

    def dump_and_compress(self):
        return self.dump()

class RDSSnapshot(Snapshot):
    def __init__(self, backup_id, config):
        self.config_id = "snapshot-rds-%s" % backup_id
        self.type = "RDSSnapshot"
        Snapshot.__init__(self, backup_id, config)

    def snapshot(self):
        logging.info("Snapshotting RDS volume %s in %s..." % (self.name, self.az))
        rdsconn = boto.rds.connect_to_region(self.az,
            aws_access_key_id=self.aws_key,
            aws_secret_access_key=self.aws_secret)
        instances = rdsconn.get_all_dbinstances(self.vol)
        db = instances[0]
        return db.snapshot('%s-%s' % (self.id, self.datestr))

class EC2Snapshot(Snapshot):
    def __init__(self, backup_id, config):
        self.config_id = "snapshot-ec2-%s" % backup_id
        self.type = "EC2Snapshot"
        Snapshot.__init__(self, backup_id, config)

    def snapshot(self):
        logging.info("Snapshotting EC2 volume %s in %s..." % (self.name, self.az))
        ec2conn = boto.ec2.connect_to_region(self.az,
            aws_access_key_id=self.aws_key,
            aws_secret_access_key=self.aws_secret)
        return ec2conn.create_snapshot(self.vol, "%s (%s)" % (self.name, self.datestr))
