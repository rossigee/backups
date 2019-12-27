import os, os.path
import datetime, time
import requests
import logging

from backups.sources import backupsource
from backups.sources.source import BackupSource
from backups.exceptions import BackupException

import adal
from msrestazure.azure_active_directory import AdalAuthentication
from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
from azure.mgmt.compute import ComputeManagementClient


@backupsource('azure-managed-disk')
class AzureManagedDisk(BackupSource):
    def __init__(self, config, type="AzureManagedDisk"):
        BackupSource.__init__(self, config, type, "disk.gpg")
        self.subscription_id = config['subscription_id']
        self.source_resource_group = config['source_resource_group']
        self.destination_resource_group = config['destination_resource_group']
        self.disk_name = config['disk_name']
        self.retain_snapshots = config['retain_snapshots']

    def dump(self):
        # Connect to Azure API
        login_endpoint = AZURE_PUBLIC_CLOUD.endpoints.active_directory
        tenant_id = os.getenv("TENANT_ID")
        client_id = os.getenv("CLIENT_ID")
        client_key = os.getenv("CLIENT_KEY")
        context = adal.AuthenticationContext(login_endpoint + '/' + tenant_id)
        credentials = AdalAuthentication(
            context.acquire_token_with_client_credentials,
            AZURE_PUBLIC_CLOUD.endpoints.active_directory_resource_id,
            client_id,
            client_key
        )
        compute_client = ComputeManagementClient(credentials, self.subscription_id)

        # Trigger a new snapshot
        now = datetime.datetime.now()
        snapshot_id = "{}-{}".format(self.disk_name, now.strftime("%Y%m%d%H%M%S"))
        logging.info("Snapshotting '%s'..." % self.disk_name)
        managed_disk = compute_client.disks.get(self.source_resource_group, self.disk_name)
        async_snapshot_creation = compute_client.snapshots.create_or_update(
            self.destination_resource_group,
            snapshot_id,
            {
                'location': managed_disk.location,
                'creation_data': {
                    'create_option': 'Copy',
                    'source_uri': managed_disk.id
                },
                'tags': {
                    'source_resource_group': self.source_resource_group,
                    'source_disk_name': self.disk_name,
                    'timestamp': time.mktime(now.timetuple()),
                    'created_by': "backups"
                }
            }
        )
        snapshot = async_snapshot_creation.result()
        logging.debug("Snapshot '%s' created in '%s'." % (snapshot.name, snapshot.location))

        # Clear down older, redundant snapshots
        logging.info("Clearing down redundant snapshots in '%s'..." % self.destination_resource_group)
        snapshot_list = compute_client.snapshots.list_by_resource_group(
            self.destination_resource_group
        )
        related_snapshots = {}
        for s in snapshot_list:
            try:
                if s.tags is None:
                    continue
                if s.tags['source_resource_group'] != self.source_resource_group:
                    continue
                if s.tags['source_disk_name'] != self.disk_name:
                    continue
                timestamp = s.tags['timestamp']
            except KeyError:
                continue
            related_snapshots[timestamp] = s
        redundant_count = len(related_snapshots) - self.retain_snapshots
        if redundant_count > 0:
            logging.info("Removing %d redundant snapshots..." % redundant_count)
            related_snapshot_ids = sorted(related_snapshots)
            for t in related_snapshot_ids[0:redundant_count]:
                s = related_snapshots[t]
                logging.debug("Revoking access to snapshot '%s'..." % s.name)
                compute_client.snapshots.revoke_access(
                    self.destination_resource_group,
                    s.name
                )
                logging.debug("Deleting snapshot '%s'..." % s.name)
                compute_client.snapshots.delete(
                    self.destination_resource_group,
                    s.name
                )

        # Obtain download URI
        logging.info("Obtaining download URI for snapshot '%s'..." % snapshot.name)
        download = compute_client.snapshots.grant_access(
            self.destination_resource_group,
            snapshot.name,
            'Read',
            7200
        )
        download_info = download.result()

        # Download
        logging.info("Downloading snapshot '%s'..." % snapshot.name)
        download_filename = '%s/%s.disk' % (self.tmpdir, self.id)
        with requests.get(download_info.access_sas, stream=True) as r:
            r.raise_for_status()
            with open(download_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                f.close()

        return [download_filename, ]
