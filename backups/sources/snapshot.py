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
    def __init__(self, config):
        BackupSource.__init__(self, config, "Snapshot", None)
        self.vol = config['volume_id']
        self.datestr = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        self.az = config['availability_zone']
        self.aws_key = config['credentials']['aws_access_key_id']
        self.aws_secret = config['credentials']['aws_secret_access_key']

    def dump(self):
        retval = self.snapshot()
        statfilename = '%s/%s.status' % (self.tmpdir, self.id)
        statfile = open(statfilename, 'wb')
        statfile.write(json.dumps({
            'status': "OK",
            'retval': str(retval)
        }))
        statfile.close()
        return [statfilename, ]

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
