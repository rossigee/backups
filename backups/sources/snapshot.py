import os, os.path
import subprocess
import boto3
import logging
import datetime
import json

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

@backupsource('snapshot')
class Snapshot(BackupSource):
    def __init__(self, config, type="Snapshot"):
        BackupSource.__init__(self, config, type, None)
        self.vol = config['volume_id']
        self.datestr = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        self.az = config['availability_zone']
        self.aws_access_key = config['credentials']['aws_access_key_id']
        self.aws_secret_key = config['credentials']['aws_secret_access_key']

    def _connect_with_boto(self, service_name):
        kwargs = dict()
        if self.credentials:
            kwargs['aws_access_key_id'] = self.aws_access_key
            kwargs['aws_secret_access_key'] = self.aws_secret_key
        return boto3.client(service_name, **kwargs)

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
        client = self._connect_with_boto("rds")

        logging.info("Snapshotting RDS volume %s in %s..." % (self.name, self.az))
        response = client.create_db_snapshot(
            DBSnapshotIdentifier='%s-%s' % (self.id, self.datestr),
            DBInstanceIdentifier=self.vol
        )
        # TODO: response handling
        print(reponse)

class EC2Snapshot(Snapshot):
    def __init__(self, backup_id, config):
        self.config_id = "snapshot-ec2-%s" % backup_id
        self.type = "EC2Snapshot"
        Snapshot.__init__(self, backup_id, config)

    def snapshot(self):
        client = self._connect_with_boto("ec2")

        logging.info("Snapshotting EC2 volume %s in %s..." % (self.name, self.az))
        instance = client.Instance(self.vol)
        image = instance.create_image(Name="%s (%s)" % (self.name, self.datestr))
        # TODO: response handling
        print(image)
