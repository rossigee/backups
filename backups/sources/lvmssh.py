import os, os.path
import subprocess
import datetime, time
import json
import logging

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException


def dev_mapper_name(vg_name, lv_name):
    def escape(s):
        return s.replace("-", "--")
    return "/dev/mapper/%s-%s" % (escape(vg_name), escape(lv_name))


@backupsource('lvm-ssh')
class LVMLogicalVolume(BackupSource):
    def __init__(self, config, type="LVM"):
        BackupSource.__init__(self, config, type, "vol.gpg")
        self.sshhost = config['sshhost']
        self.sshuser = config['sshuser']
        self.vg_name = config['vg_name']
        self.lv_name = config['lv_name']
        self.size = config['size']
        self.retain_snapshots = config['retain_snapshots']

    def dump(self):
        # Identify snapshot source device
        snapshot_dev = dev_mapper_name(self.vg_name, self.lv_name)

        # Trigger a new snapshot
        now = datetime.datetime.now()
        snapshot_id = "{}-{}".format(self.lv_name, now.strftime("%Y%m%d%H%M%S"))
        logging.info("Snapshotting '%s'..." % self.lv_name)
        snapshotargs = [
            'ssh', ('%s@%s' % (self.sshuser, self.sshhost)),
            'lvcreate', ('-L%s' % self.size), '-s', '-n', snapshot_id, snapshot_dev
        ]
        logging.debug("Running '%s'" % (" ".join(snapshotargs)))
        snapshotproc = subprocess.Popen(snapshotargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if snapshotproc.stdin:
            snapshotproc.stdin.close()
        snapshotproc.wait()
        exitcode = snapshotproc.returncode
        outmsg = snapshotproc.stdout.read()
        #print("OUT: %s" % outmsg)
        errmsg = snapshotproc.stderr.read()
        #print("ERR: %s" % errmsg)
        if errmsg != b'':
            logging.error(errmsg)
        if exitcode > 1:
            raise BackupException("Error while snapshotting (exitcode %d): %s" % (exitcode, errmsg))
        logging.debug("Snapshot '%s' created." % snapshot_id)

        # Fetching list of snapshots
        logging.info("Fetching list of snapshots...")
        snapshotlistargs = [
            'ssh', ('%s@%s' % (self.sshuser, self.sshhost)),
            'lvs', '-S', ('origin=\"%s\"' % self.lv_name),
            '--reportformat', 'json'
        ]
        logging.debug("Running '%s'" % (" ".join(snapshotlistargs)))
        snapshotlistproc = subprocess.Popen(snapshotlistargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if snapshotlistproc.stdin:
            snapshotlistproc.stdin.close()
        snapshotlistproc.wait()
        exitcode = snapshotlistproc.returncode
        outmsg = snapshotlistproc.stdout.read()
        #print("OUT: %s" % outmsg)
        errmsg = snapshotlistproc.stderr.read()
        #print("ERR: %s" % errmsg)
        if errmsg != b'':
            logging.error(errmsg)
        if exitcode > 1:
            raise BackupException("Error while listing snapshots (exitcode %d): %s" % (exitcode, errmsg))
        lvs = json.loads(outmsg)['report'][0]['lv']
        snapshots = [lv['lv_name'] for lv in lvs]
        logging.info("Found %d snapshots." % len(snapshots))

        # Clear down older, redundant snapshots
        logging.info("Clearing down redundant snapshots...")
        redundant_count = len(snapshots) - self.retain_snapshots
        if redundant_count > 0:
            logging.info("Removing %d redundant snapshots..." % redundant_count)
            lvm_ids = sorted(snapshots)
            for lvm_id in lvm_ids[0:redundant_count]:
                logging.debug("Deleting volume snapshot '%s'..." % lvm_id)
                snapshotremoveargs = [
                    'ssh', ('%s@%s' % (self.sshuser, self.sshhost)),
                    'lvremove', '-f', dev_mapper_name(self.vg_name, lvm_id),
                ]
                logging.debug("Running '%s'" % (" ".join(snapshotremoveargs)))
                snapshotremoveproc = subprocess.Popen(snapshotremoveargs, stderr=subprocess.PIPE)
                if snapshotremoveproc.stdin:
                    snapshotremoveproc.stdin.close()
                snapshotremoveproc.wait()
                exitcode = snapshotremoveproc.returncode
                errmsg = snapshotremoveproc.stderr.read()
                if errmsg != b'':
                    logging.error(errmsg)
                if exitcode > 1:
                    raise BackupException("Error while removing snapshot ''%s' (exitcode %d): %s" % (lvm_id, exitcode, errmsg))

        # Stream volume down to a local file
        logging.info("Downloading volume for snapshot '%s'..." % snapshot_id)
        dumpfilename = '%s/%s.dump' % (self.tmpdir, self.lv_name)
        dumpfile = open(dumpfilename, 'wb')
        dumpargs = [
            'ssh', ('%s@%s' % (self.sshuser, self.sshhost)),
            'dd', ('if=%s' % dev_mapper_name(self.vg_name, snapshot_id)), "status=none"
        ]
        logging.debug("Running '%s'" % (" ".join(dumpargs)))
        dumpproc1 = subprocess.Popen(dumpargs, stdout=dumpfile, stderr=subprocess.PIPE)
        if dumpproc1.stdin:
            dumpproc1.stdin.close()
        dumpproc1.wait()
        exitcode = dumpproc1.returncode
        errmsg = dumpproc1.stderr.read()
        if errmsg != b'':
            logging.error(errmsg)
        if exitcode > 1:
            raise BackupException("Error while dumping (exitcode %d): %s" % (exitcode, errmsg))

        dumpfile.close()

        return [dumpfilename, ]
