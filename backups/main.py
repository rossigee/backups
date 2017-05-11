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

import backups.stats
import backups.sources
import backups.destinations
import backups.notifications

from backups.exceptions import BackupException

RUN_AS_USER=os.getenv('BACKUP_RUN_AS_USER', 'backups')

# Default set of modules to import
default_modules = [
    'backups.sources.folder',
    'backups.sources.mysql',
    'backups.sources.postgresql',
    'backups.sources.rds',
    'backups.sources.snapshot',
    'backups.destinations.s3',
    'backups.destinations.samba',
    'backups.notifications.flagfile',
    'backups.notifications.hipchat',
    'backups.notifications.prometheus',
    'backups.notifications.slack',
    'backups.notifications.smtp',
    'backups.notifications.telegram',
]

class BackupRunInstance:
    def __init__(self, hostname = 'localhost'):
        self.hostname = hostname
        self.source_modules = []
        self.sources = []
        self.destination_modules = []
        self.destinations = []
        self.notification_modules = []
        self.notifications = []

        self.stats = backups.stats.BackupRunStatistics()

    def run(self):
        # Loop through the defined source modules...
        for source in self.sources:
            # Trigger notifications as required
            for notification in self.notifications:
                notification._notify_start(source, self.hostname)

            try:
                # Dump and compress
                starttime = time.time()
                dumpfiles = source.dump_and_compress()
                if not isinstance(dumpfiles, list):
                    dumpfiles = [dumpfiles, ]
                endtime = time.time()
                self.stats.dumptime = endtime - starttime

                # Add up backup file sizes
                totalsize = 0
                for dumpfile in dumpfiles:
                    totalsize = totalsize + os.path.getsize(dumpfile)
                self.stats.size = totalsize

                # Send each dump file to each listed destination
                starttime = time.time()
                for dumpfile in dumpfiles:
                    for destination in self.destinations:
                        destination.send(source.id, source.name, source.suffix, dumpfile)
                        destination.cleanup(source.id, source.name, source.suffix, self.stats)
                endtime = time.time()
                self.stats.uploadtime = endtime - starttime

                # Trigger success notifications as required
                for notification in self.notifications:
                    notification._notify_success(source, self.hostname, dumpfile, self.stats)

            except Exception as e:
                import traceback
                traceback.print_exc()
                # Trigger notifications as required
                for notification in self.notifications:
                    notification._notify_failure(source, self.hostname, e)

            finally:
                # Done with the dump file now
                if 'dumpfile' in locals() and os.path.isfile(dumpfile):
                   os.unlink(dumpfile)

        logging.debug("Complete.")

# Special configuration file parser that can check for envvars as a fallback
# where a value is not specified in the config file
class EnvvarConfigParser(ConfigParser.RawConfigParser):
    def get_or_envvar(self, section, option, envvarname):
        try:
            val = self.get(section, option)
            if val is not None:
                return val
        except:
            pass
        if envvarname not in os.environ:
            return None
        return os.environ[envvarname]

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
        parser.add_argument('-d', dest='debug', action='store_true')
        args = parser.parse_args()
        configfile = args.configfile[0]

        # Enable logging if verbosity requested
        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
        elif args.verbose:
            logging.basicConfig(level=logging.INFO)

        # Read our configuration file our special config handler
        config = EnvvarConfigParser()
        config.read(configfile)

        # Determine hostname
        hostname = config.get_or_envvar('defaults', 'hostname', 'BACKUPS_HOSTNAME')

        # Import main and additional handler library modules
        backup_modules = config.get_or_envvar('defaults', 'backup_modules', "BACKUP_MODULES")
        if backup_modules is not None:
            backup_modules = backup_modules.split(',')
        else:
            backup_modules = default_modules
        for modulename in backup_modules:
            logging.debug("Importing module '%s'" % modulename)
            try:
                module = __import__(modulename)
            except ImportError as e:
                logging.error("Error importing module: %s" % e.__str__())

        # Instantiate handlers for any listed destinations
        destinations = []
        for dest_id, dest_class in backups.destinations.handlers.items():
            logging.debug("Dest(%s) - %s" % (dest_id, dest_class))
            for section in config.sections():
                if section == dest_id:
                    destination = dest_class(config)
                    destinations.append(destination)

        # Instantiate handlers for any listed notifications
        notifications = []
        for notify_id, notify_class in backups.notifications.handlers.items():
            logging.debug("Notify(%s) - %s" % (notify_id, notify_class))
            for section in config.sections():
                if section == notify_id:
                    notification = notify_class(config)
                    notifications.append(notification)

        # Loop through sections, process those we have sources for
        sources = []
        for source_id, source_class in backups.sources.handlers.items():
            logging.debug("Source(%s) - %s" % (source_id, source_class))
            for section in config.sections():
                if section.startswith(source_id + "-"):
                    backup_id = section[(len(source_id) + 1):]
                    source = source_class(backup_id, config)
                    sources.append(source)

        if len(sources) < 1:
            raise BackupException("No sources listed in configuration file.")

        instance = BackupRunInstance(hostname)
        instance.notifications = notifications
        instance.sources = sources
        instance.destinations = destinations
        instance.run()

    except KeyboardInterrupt :
        sys.exit()

if __name__ == '__main__':
    main()
