#!/usr/bin/env python

import os
import os.path
import sys
import contextlib
import datetime
import time
import traceback
import argparse
import getpass
import logging
import logging.handlers
import json

# OpenTelemetry imports (optional SDK/exporter; shim used when unavailable)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    OTEL_AVAILABLE = True
except ImportError:
    trace = None
    OTEL_AVAILABLE = False

import backups.stats
import backups.sources
import backups.destinations
import backups.notifications

from backups.exceptions import BackupException

try:
    from importlib.metadata import version as _pkg_version
    _SERVICE_VERSION = _pkg_version("backups")
except Exception:
    _SERVICE_VERSION = "unknown"


class _NoOpSpan:
    def set_attribute(self, *args, **kwargs): pass
    def record_exception(self, *args, **kwargs): pass
    def set_status(self, *args, **kwargs): pass


class _NoOpTracer:
    @contextlib.contextmanager
    def start_as_current_span(self, name, **kwargs):
        yield _NoOpSpan()


# Default set of modules to import
default_modules = [
    'backups.sources.azure_managed_disk',
    'backups.sources.folder',
    'backups.sources.mysql',
    'backups.sources.postgresql',
    'backups.sources.rds',
    'backups.sources.snapshot',
    'backups.destinations.s3',
    'backups.destinations.samba',
    'backups.notifications.flagfile',
    'backups.notifications.discord',
    'backups.notifications.elasticsearch',
    'backups.notifications.prometheus',
    'backups.notifications.matrix',
    'backups.notifications.slack',
    'backups.notifications.smtp',
    'backups.notifications.telegram',
]

class BackupRunInstance:
    def __init__(self):
        import platform
        self.hostname = platform.node()
        self.source_modules = []
        self.sources = []
        self.destination_modules = []
        self.destinations = []
        self.notification_modules = []
        self.notifications = []

        self.stats = backups.stats.BackupRunStatistics()
        self.tracer = _NoOpTracer()

    def run(self):
        with self.tracer.start_as_current_span("backup_run") as root_span:
            root_span.set_attribute("hostname", self.hostname)

            for source in self.sources:
                with self.tracer.start_as_current_span("process_source") as source_span:
                    source_span.set_attribute("source.id", source.id)
                    source_span.set_attribute("source.name", source.name)
                    source_span.set_attribute("hostname", self.hostname)

                    for notification in self.notifications:
                        with self.tracer.start_as_current_span("notify_start") as notify_span:
                            notify_span.set_attribute("notification.type", notification.__class__.__name__)
                            try:
                                notification._notify_start(source, self.hostname)
                            except Exception as e:
                                logging.error("Error sending start notification (%s): %s", type(notification), e)

                    try:
                        starttime = time.time()
                        self.stats.starttime = datetime.datetime.now()
                        with self.tracer.start_as_current_span("dump_and_compress") as dump_span:
                            dumpfiles = source.dump_and_compress(self.stats)
                            if not isinstance(dumpfiles, list):
                                dumpfiles = [dumpfiles]
                            endtime = time.time()
                            self.stats.dumptime = endtime - starttime
                            totalsize = sum(os.path.getsize(f) for f in dumpfiles)
                            self.stats.size = totalsize
                            dump_span.set_attribute("dumptime", self.stats.dumptime)
                            dump_span.set_attribute("file.count", len(dumpfiles))
                            dump_span.set_attribute("total.size", totalsize)

                        starttime = time.time()
                        self.stats.dumpedfiles = []
                        self.stats.retainedfiles = []
                        with self.tracer.start_as_current_span("upload_files") as upload_span:
                            for dumpfile in dumpfiles:
                                for destination in self.destinations:
                                    uploaded = destination.send(source.id, source.name, dumpfile)
                                    self.stats.dumpedfiles.append(uploaded)
                                    retained = destination.cleanup(source.id, source.name)
                                    self.stats.retainedfiles += retained
                            endtime = time.time()
                            self.stats.endtime = datetime.datetime.now()
                            self.stats.uploadtime = endtime - starttime
                            upload_span.set_attribute("uploadtime", self.stats.uploadtime)
                            upload_span.set_attribute("dumped.count", len(self.stats.dumpedfiles))
                            upload_span.set_attribute("retained.count", len(self.stats.retainedfiles))

                        for notification in self.notifications:
                            with self.tracer.start_as_current_span("notify_success") as notify_span:
                                notify_span.set_attribute("notification.type", notification.__class__.__name__)
                                try:
                                    notification._notify_success(source, self.hostname, dumpfile, self.stats)
                                except Exception as e:
                                    logging.error("Error sending success notification (%s): %s", type(notification), e)

                    except Exception as e:
                        traceback.print_exc()
                        source_span.record_exception(e)
                        if OTEL_AVAILABLE:
                            source_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        for notification in self.notifications:
                            with self.tracer.start_as_current_span("notify_failure") as notify_span:
                                notify_span.set_attribute("notification.type", notification.__class__.__name__)
                                notify_span.set_attribute("error", str(e))
                                try:
                                    notification._notify_failure(source, self.hostname, e)
                                except Exception as e2:
                                    logging.error("Error sending failure notification (%s): %s", type(notification), e2)
                                    logging.error("Original error was: %s", e)

                    finally:
                        if 'dumpfile' in locals() and os.path.isfile(dumpfile):
                            os.unlink(dumpfile)

            logging.debug("Complete.")

def main():
    try:
        # Make doubly sure temp files aren't world-viewable
        os.umask(int('077', 8))

        # Read command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('configfile', metavar='configfile', nargs=1,
                   help='name of configuration file to use for this run')
        parser.add_argument('-v', dest='verbose', action='store_true')
        parser.add_argument('-d', dest='debug', action='store_true')
        args = parser.parse_args()
        configfile = args.configfile[0]

        # Initialize OpenTelemetry tracing if OTEL_EXPORTER_OTLP_ENDPOINT is set
        otel_tracer = _NoOpTracer()
        trace_provider = None
        if OTEL_AVAILABLE and os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            resource = Resource.create({
                SERVICE_NAME: "backups",
                "service.version": _SERVICE_VERSION,
            })
            # TracerProvider respects OTEL_TRACES_SAMPLER / OTEL_TRACES_SAMPLER_ARG env vars
            trace_provider = TracerProvider(resource=resource)
            insecure = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "false").lower() == "true"
            otlp_exporter = OTLPSpanExporter(
                endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
                insecure=insecure,
            )
            trace_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(trace_provider)
            otel_tracer = trace.get_tracer("backups.tracer")
            logging.info("OpenTelemetry tracing enabled.")

        # Enable logging if verbosity requested
        if args.debug:
            logging.basicConfig(level=logging.DEBUG)
        elif args.verbose:
            logging.basicConfig(level=logging.INFO)

        # Read our JSON configuration file
        with open(configfile) as json_conf:
            config = json.load(json_conf)

        # Import main and additional handler library modules
        backup_modules = config['modules']
        if backup_modules is None:
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
            for dest_config in config['destinations']:
                if dest_config['type'] == dest_id:
                    destination = dest_class(dest_config)
                    destinations.append(destination)

        # Instantiate handlers for any listed notifications
        notifications = []
        for notify_id, notify_class in backups.notifications.handlers.items():
            logging.debug("Notify(%s) - %s" % (notify_id, notify_class))
            for notify_config in config['notifications']:
                if notify_config['type'] == notify_id:
                    notification = notify_class(notify_config)
                    notifications.append(notification)

        # Loop through sections, process those we have sources for
        sources = []
        for source_id, source_class in backups.sources.handlers.items():
            logging.debug("Source(%s) - %s" % (source_id, source_class))
            for source_config in config['sources']:
                if source_config['type'] == source_id:
                    source = source_class(source_config)
                    sources.append(source)

        if len(sources) < 1:
            raise BackupException("No sources listed in configuration file.")

        instance = BackupRunInstance()
        instance.notifications = notifications
        instance.sources = sources
        instance.destinations = destinations
        instance.tracer = otel_tracer
        instance.run()

        # Shutdown tracing if enabled
        if trace_provider is not None:
            trace_provider.shutdown()
            logging.info("OpenTelemetry tracing shut down.")

    except KeyboardInterrupt :
        sys.exit()

if __name__ == '__main__':
    main()
