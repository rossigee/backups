#!/usr/bin/env python

import os
import os.path
import sys
import time
import argparse
import getpass
import logging
import logging.handlers
import ConfigParser

import backups.folder
import backups.mysql
import backups.rds
import backups.s3
import backups.samba
import backups.smtp
import backups.snapshot
import backups.hipchat
import backups.slack
import backups.telegram
import backups.flagfile
import backups.stats

from backups.exceptions import BackupException

RUN_AS_USER=os.getenv('BACKUP_RUN_AS_USER', 'backups')

class BackupRunInstance:
    def __init__(self):
        self.hostname = 'localhost'
        self.notifications = []
        self.sources = []
        self.destinations = []

        self.stats = backups.stats.BackupRunStatistics()

    def run(self):
        # Loop through the defined sources...
        for source in self.sources:
            try:
                # Dump and compress
                starttime = time.time()
                dumpfile = source.dump_and_compress()
                endtime = time.time()
                self.stats.dumptime = endtime - starttime
                self.stats.size = os.path.getsize(dumpfile)

                # Send to each listed destination
                starttime = time.time()
                for destination in self.destinations:
                    destination.send(dumpfile, source.name)
                endtime = time.time()
                self.stats.uploadtime = endtime - starttime

                # Trigger success notifications as required
                for notification in self.notifications:
                    notification.notify_success(source.name, source.type, self.hostname, dumpfile, self.stats)

            except Exception as e:
                # Trigger notifications as required
                for notification in self.notifications:
                    notification.notify_failure(source.name, source.type, self.hostname, e)

            finally:
                # Done with the dump file now
                if 'dumpfile' in locals() and os.path.isfile(dumpfile):
                   os.unlink(dumpfile)

        logging.debug("Complete.")

def main():
    try:
        # User check
        if getpass.getuser() != RUN_AS_USER:
            sys.exit("ERROR: Must be run as '%s' user." % RUN_AS_USER)

        # Make doubly sure temp files aren't world-viewable
        os.umask(077)

        # Read command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('configfile', metavar='configfile', nargs=1,
                   help='name of configuration file to use for this run')
        parser.add_argument('-v', dest='verbose', action='store_true')
        args = parser.parse_args()
        configfile = args.configfile[0]

        # Read our configuration file
        config = ConfigParser.RawConfigParser()
        config.read(configfile)

        # Create an instance, configure and run it
        defaults = config.items('defaults')

        # Instantiate handlers for any listed destinations
        destinations = []
        for section in config.sections():
            if section == 's3':
                destination = backups.s3.S3(config)
                destinations.append(destination)
            if section == 'samba':
                destination = backups.samba.Samba(config)
                destinations.append(destination)

        # Instantiate handlers for any listed notifications
        notifications = []
        for section in config.sections():
            if section == 'smtp':
                notification = backups.smtp.SMTP(config)
                notifications.append(notification)
            if section == 'hipchat':
                notification = backups.hipchat.Hipchat(config)
                notifications.append(notification)
            if section == 'slack':
                notification = backups.slack.Slack(config)
                notifications.append(notification)
            if section == 'telegram':
                notification = backups.telegram.Telegram(config)
                notifications.append(notification)
            if section == 'flagfile':
                notification = backups.flagfile.Flagfile(config)
                notifications.append(notification)

        # Loop through sections, process those we have sources for
        sources = []
        for section in config.sections():
            if section[0:7] == 'folder-':
                backup_id = section[7:]
                source = backups.folder.Folder(backup_id, config)
                sources.append(source)
            if section[0:6] == 'mysql-':
                backup_id = section[6:]
                source = backups.mysql.MySQL(backup_id, config)
                sources.append(source)
            if section[0:4] == 'rds-':
                backup_id = section[4:]
                source = backups.rds.RDS(backup_id, config)
                sources.append(source)
            if section[0:13] == 'snapshot-ec2-':
                backup_id = section[13:]
                source = backups.snapshot.EC2Snapshot(backup_id, config)
                sources.append(source)
            if section[0:13] == 'snapshot-rds-':
                backup_id = section[13:]
                source = backups.snapshot.RDSSnapshot(backup_id, config)
                sources.append(source)

        if len(sources) < 1:
            raise BackupException("No sources listed in configuration file.")

        instance = BackupRunInstance()
        instance.hostname = config.get('defaults', 'hostname')
        instance.notifications = notifications
        instance.sources = sources
        instance.destinations = destinations
        instance.run()

    except KeyboardInterrupt :
        sys.exit()

if __name__ == '__main__':
    main()
