Backup scripts
==============

This python script, given a backup configuration, will cycle through a list of backup 'sources', packing them up and encrypting them into a temporary file, which it will upload to each of a list of destinations, finally reporting success or failure via a list of notification handlers.

Overview
--------

Roughly speaking there are 'sources', 'destinations' and 'notifications'.

Currently implemented sources are:

* folders (using tar)
* folders via SSH (using tar)
* MySQL databases (using mysqldump)
* MySQL databases via SSH (using mysqldump)
* PostgreSQL databases (using pg_dump)
* RDS MySQL database snapshots (using mysqldump)
* RDS PostgreSQL database snapshots (using pg_dump)
* Azure Managed Disks
* LVM snapshots over SSH

Currently implemented destinations are:

* an S3 bucket (uses aws-cli)
* a GS bucket (uses gsutil)
* a Samba share (uses smbclient)
* a local filesystem path
* a Backblaze B2 bucket (uses b2sdk)
* a Minio/S3-compatible bucket (uses minio SDK; works with DigitalOcean Spaces etc.)
* a Dropbox folder (uses dropbox SDK)
* a Google Drive folder (uses google-api-python-client with service account)

Currently implemented notifications are:

* an e-mail (via smtplib)
* a HipChat room notification
* a Discord room notification
* a Slack notification
* a Telegram notification
* a simple flag file
* a Prometheus push gateway
* an Elasticsearch index

Hopefully, it's fairly straightforward to extend or add to the above.

The sources will be used to generate dump files in a temporary working area. By default, this is '/var/tmp', but for large DB dumps, you may need to specify an alternative folder mounted somewhere with enough space to store a compressed dump, and it's encrypted equivalent, temporarily.

Backups will be encrypted with a given passphrase (using GnuPG), and put into a folder on the destination using the following filename pattern...

    /{hostname}/{yyyy-mm-dd}/{dumpfile_id}.{sql|tar}.gpg

If the backup configuration specifies a retention policy, then any copies that exist on the backup destination that fall outside that scope are deleted. Typically, a retention policy will specify to keep a copies for a certain number of days, or just a number of the most recent copies.

If encryption is not needed or desired, you may specify that only compression is used. Note that this will not safeguard the contents of the file should someone gain access to it. Compression is performed using gzip --fast and can be specfied in the source configuration using...

    "compress_only": 1

Also, a word to the wise about scheduling. Backing up large chunks of data can use a lot of resources, and even if set to run after 'work' hours, can often run for on into the morning and indeed the next working day. Break larger backups down into smaller chunks where possible. If you are backing up mission criticial servers over mission critical network connections, you may need to take additional precautions to ensure that your backup scripts are not going to cause knock-on problems. You have been warned.

For security purposes, the script is designed to run as a non-privileged user. By default, it expects to be run as the 'backups' user, but this can be overridden using the 'RUN_AS_USER' environment variable.


Installation
------------

1. Install me. Unpack me, run `pip install .` as root (or in a virtualenv).

1. Create a configuration file listing the folders/databases you want to back up, an encryption passphrase, and one or more places you want the encrypted dump file uploaded to, and details of any notification methods you wish to use. See docs further down for examples. You can install the dependencies now, or you can wait until you get errors later :)

1. Create a 'backups' user to run the script as. If you need folders to be backed up that require superuser privileges, you will also need a 'sudoers' directive to allow the backups user to run 'tar' as root to do it's work.

```
# cat >/etc/sudoers.d/99-backups <<EOF
backups ALL=(ALL) NOPASSWD: /bin/tar
EOF
```

1. Test your configuration by doing an initial run of the backup.

``` bash
# sudo -H -u backups /usr/local/bin/backup -v /home/backups/mynightlybackup.cfg
```

1. Add your job to cron.

```
# cat >/etc/cron.d/nightly-backups.conf <<EOF
0 2 * * * backups /usr/local/bin/backup /home/backups/mynightlybackup.cfg
EOF
```

You're done.


Example configuration
---------------------

IMPORTANT: The configuration file may contain sensitive information. Be sure to keep it somewhere safe, with suitable permissions.

To keep things simple, backup jobs are defined as JSON files, and are passed in at runtime.

The root object will contain the default settings that are not specific to a particular source, destination or notification.

```json
{
  "hostname": "my.hostname.com",
  "tmpdir": "/var/tmp/backups",
  "modules": [],
  "sources": [],
  "destinations": [],
  "notifications": [],
}
```

Parameters available in the root object:

| Config key | Purpose |
|------------|---------|
| hostname | Used to help identify the folder the backup should be stored in on the destination. |
| tmpdir | Somewhere with enough temporary space to contain the compressed backup and it's encrypted copy as it's being built. |
| modules | A list of modules to load to handle this job. |
| sources | A list of sources to collect backup data from. |
| destinations | A list of destinations to push backup data to. |
| notifications | A list of mechanisms by which to report success/failure. |


Common Source parameters
------------------------

| Config key | Purpose |
|------------|---------|
| passphrase | A passphrase to encrypt the backup with (using GnuPG). |
| recipients | (Optional) If recipients are provided, the encrypted backup is encrypted for the list of recipients specified. If recipients are not provided, the backup symetrically encrypted using the given passphrase |


Source - Folder
---------------

You can specify one or more folders to be backed up.

The 'modules' paramter must contain the `backups.sources.folder` module and there should be one or more source objects such as:

```json
{
  "id": "accountsdata",
  "name": "Live Accounts Data",
  "type": "folder",
  "path": "/var/lib/myaccountspkg/data"
}
```

You can specify an array of `--exclude` parameters to tell tar which folders/files to exclude too.

```json
{
  "id": "accountsdata",
  "name": "Live Accounts Data",
  "type": "folder",
  "path": "/var/lib/myaccountspkg/data",
  "excludes": [
    "tmp",
    "*~"
  ]
}
```

Parameters available in 'folder':

| Config key |  Purpose |
|------------|----------|
| name |  Description of data being backed up (for reporting purposes). |
| path | Name of file or folder to be backed up. |
| excludes | One or more files/paths to be excluded from the backup. |


Source - MySQL Database
-----------------------

You can specify one or more mySQL databases to be backed up.

The 'modules' paramter must contain the `backups.sources.mysql` module and there should be one or more source objects such as:

```json
{
  "id": "livecompanydb",
  "name": "Live Company Data",
  "type": "mysql",
  "dbhost": "localhost",
  "dbname": "livecompany",
  "dbuser": "backups",
  "dbpass": "zzzuserwithreadonlyperms",
  "passphrase": "64b0c7405f2d8051e2b9f02aa4898acc",
  "compress_only": 1
}
```

The script creates a temporary 'mysqlclient' credentials file using the given details, and passes it as the '--defaults-file' argument.

By default, the '--events' flag is passed to mysqldump. This may break older versions of mysqldump (prior to version 5.1, IIRC), so you can disable this flag with the 'noevents' parameter. I hope you aren't using versions of MySQL that old!

```
[client]
host=specific.host.database.com
...
noevents=1
```

If supplied, directives should be a single string with all options seperated with a space.
For example:

```json
{
  "options": "--all-databases --single-transaction --skip-triggers"
}
```

NOTE: If you pass --all-databases as a directive, dbname will be ignored.

Parameters available in 'mysql':

| Config key | Purpose |
|------------|---------|
| name | Description of data being backed up (for reporting purposes). |
| dbhost | Name of the mySQL host to connect to. |
| dbname | Name of the mySQL database to back up. You may specify more than one. |
| dbuser | Username to connect to mySQL as. |
| dbpass | Password to connect to mySQL with. |
| defaults | The location of an 'mysqlclient' credentials file to use instead of creating a temporary one with using above 'db*' variables. |
| options | An optional string of options to pass to 'mysqldump'. |
| noevents | Don't pass the '--events' flag to 'mysqldump'. |


Source - PostgreSQL Database
----------------------------

You can specify one of more PostgreSQL databases to be backed up.

```json
{
  "id": "livecompanydb",
  "name": "Live Company Data",
  "type": "pgsql",
  "dbhost": "localhost",
  "dbname": "livecompany",
  "dbuser": "backups",
  "dbpass": "zzzuserwithreadonlyperms",
  "passphrase": "64b0c7405f2d8051e2b9f02aa4898acc"
}
```

The script creates a temporary 'pgpass' credentials file using the given details.

Parameters available in 'pgsql':

| Config key | Purpose |
|------------|---------|
| name | Description of data being backed up (for reporting purposes). |
| dbhost | Name of the PostgreSQL host to connect to. |
| dbname | Name of the PostgreSQL database to back up. |
| dbuser | Username to connect to PostgreSQL as. |
| dbpass | Password to connect to PostgreSQL with. |


Source - RDS MySQL Database Snapshots
-------------------------------------

You can specify one or more Amazon RDS MySQL instances to be backed up using automated snapshots. The most recent automatic snapshot is restored to a temporary RDS instance, `mysqldump` is run against it, then the temporary instance is deleted. This avoids any load on the live database.

WARNING: This can take a very long time.

```json
{
  "id": "livecompanydb",
  "name": "Live Company Data",
  "type": "rds",
  "instancename": "livedb1",
  "region": "eu-west-1",
  "security_group": "sg-xxxxxxxx",
  "instance_class": "db.t3.small",
  "dbname": "livecompany",
  "dbuser": "backups",
  "dbpass": "zzzuserwithreadonlyperms",
  "passphrase": "64b0c7405f2d8051e2b9f02aa4898acc"
}
```

AWS credentials are taken from the environment or `~/.aws/credentials`. You can also supply them directly in the config:

```json
{
  "credentials": {
    "aws_access_key_id": "YOURACCESSKEY",
    "aws_secret_access_key": "YOURSECRETKEY"
  }
}
```

The `security_group` must allow inbound access from the host running this script.

Parameters available in 'rds':

| Config key | Purpose |
|------------|---------|
| name | Description of data being backed up (for reporting purposes). |
| instancename | RDS instance identifier to restore a snapshot of. |
| region | AWS region of the RDS instance. |
| security_group | VPC security group ID to assign to the temporary instance. |
| instance_class | RDS instance class for the temporary instance (default: `db.t3.small`). |
| dbname | MySQL database name to dump. |
| dbuser | MySQL username. |
| dbpass | MySQL password. |
| noevents | Don't pass the `--events` flag to `mysqldump`. |
| credentials | Object with `aws_access_key_id` and `aws_secret_access_key` (optional). |


Source - RDS PostgreSQL Database Snapshots
------------------------------------------

Identical workflow to the RDS MySQL source above, but uses `pg_dump` instead of `mysqldump`. Use `type: rds-pgsql`.

```json
{
  "id": "livecompanydb",
  "name": "Live Company Data",
  "type": "rds-pgsql",
  "instancename": "livedb1",
  "region": "eu-west-1",
  "security_group": "sg-xxxxxxxx",
  "instance_class": "db.t3.small",
  "dbname": "livecompany",
  "dbuser": "backups",
  "dbpass": "zzzuserwithreadonlyperms",
  "passphrase": "64b0c7405f2d8051e2b9f02aa4898acc"
}
```

Parameters available in 'rds-pgsql':

| Config key | Purpose |
|------------|---------|
| name | Description of data being backed up (for reporting purposes). |
| instancename | RDS instance identifier to restore a snapshot of. |
| region | AWS region of the RDS instance. |
| security_group | VPC security group ID to assign to the temporary instance. |
| instance_class | RDS instance class for the temporary instance (default: `db.t3.small`). |
| dbname | PostgreSQL database name to dump. |
| dbuser | PostgreSQL username. |
| dbpass | PostgreSQL password. |
| credentials | Object with `aws_access_key_id` and `aws_secret_access_key` (optional). |


Source - Volume snapshots
-------------------------

This method allows us to specify a set of RDS/EC2 volumes. When sourced, this will issue snapshot commands for the volumes or instances specified.

```json
{
  "id": "livecompanydb",
  "name": "Live Company Data",
  "type": "snapshot",
  "instancename": "maindb1",
  "credentials": {
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY"
  }
}
```

It leaves a temporary file with status details as a 'dumpfile'. This gives the destination plugin something to work with when reporting success.

This source plugin is best used in a configuration on it's own, or with other volume snapshot definitions only, as used with a destination but no payload the configuration wouldn't make much sense!

NOTE: This plugin is largely unused and unmaintained at present.


Parameters available in 'snapshot':

| Config key | Purpose |
|------------|---------|
| name | Description of data being backed up (for reporting purposes). |
| volume_id | ID of the EBS volume to be snapshotted. |
| availability_zone | AWS availability zone. |
| aws_access_key_id | AWS access key. |
| aws_secret_access_key | AWS secret access key. |


Source - Azure Managed Disks
----------------------------

This method uses the Azure API to create a snapshot of the specified managed disk.

```json
{
  "id": "mydisk1",
  "type": "azure-managed-disk",
  "name": "My Disk 1",
  "subscription_id": "285adaab-abcd-41cc-1234-9f256543d534",
  "source_resource_group": "MC_KUBERNETES_AZURECLUSTER1_NORTHEUROPE",
  "destination_resource_group": "MyBackupsResourceGroup",
  "disk_name": "mydisk1",
  "retain_snapshots": 3
}
```

The `retain_snapshots` ensures that a certain number of recent snapshots are left on Azure.

Parameters available in 'azure-managed-disk':

| Config key | Purpose |
|------------|---------|
| subscription_id | The Azure subscription ID |
| source_resource_group | The RG that the managed disk resides in |
| destination_resource_group | The RG that the snapshot should be created in |
| disk_name | The name of the managed disk in the source RG |
| retain_snapshots | How many snapshots to leave in place on Azure |

Additionally, the following environment variables must be defined for authentication (from AD service principal):

| Env var | Description |
|---------|-------------|
| TENANT_ID | Azure Tenant ID |
| CLIENT_ID | Azure client/app ID |
| CLIENT_KEY | Azure client secret key |


Source - LVM over SSH
---------------------

This method calls LVM commands over SSH to obtain a snapshot of an LVM volume.

```json
{
  "id": "mydisk1",
  "type": "lvm-ssh",
  "name": "My Disk 1",
  "sshhost": "hostname.domain.com",
  "sshuser": "root",
  "vg_name": "ubuntu-vg",
  "lv_name": "mydisk1",
  "size": "5G",
  "retain_snapshots": 3
}
```

The `retain_snapshots` ensures that a certain number of snapshot volumes are retained on the host.

Parameters available in 'lvm-ssh':

| Config key | Purpose |
|------------|---------|
| sshhost | The hostname to SSH to |
| sshuser | The username to SSH with |
| vg_name | The volume group name |
| lv_name | The logical volume name |
| size | The logical volume size |
| retain_snapshots | How many snapshot volumes to leave in place |


Destination - S3
----------------

You can specify an S3 bucket to back up to.

```json
{
  "id": "s3-backup",
  "type": "s3",
  "bucket": "my-backup-bucket",
  "region": "eu-west-1",
  "credentials": {
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY"
  },
  "retention_copies": 7,
  "retention_days": 30
}
```

If `credentials` are omitted, the AWS CLI will fall back to the standard credential chain (`~/.aws/credentials`, IAM instance role, environment variables, etc.).

For S3-compatible services (e.g. MinIO, Wasabi), supply `endpoint_url`:

```json
{
  "endpoint_url": "https://s3.wasabisys.com"
}
```

Parameters available in 's3':

| Config key | Purpose |
|------------|---------|
| bucket | S3 bucket name. |
| region | AWS region. |
| credentials.aws_access_key_id | AWS access key ID (optional). |
| credentials.aws_secret_access_key | AWS secret access key (optional). |
| retention_copies | How many copies of older backups to keep. |
| retention_days | How many days of backups to keep. |
| endpoint_url | S3-compatible endpoint URL (optional). |


Destination - GS
----------------

You can specify a Google Cloud Storage bucket to back up to. Uploads use `gsutil` and retention management uses the `google-cloud-storage` Python SDK.

```json
{
  "id": "gcs-backup",
  "type": "gs",
  "bucket": "my-backup-bucket",
  "gcs_creds_path": "/etc/backups/gcs-service-account.json",
  "retention_copies": 7,
  "retention_days": 30
}
```

Create a GCP service account with Storage Object Admin on the target bucket, download the JSON key file, and place it on the backup host. Ensure `gsutil` is authenticated with the same service account (e.g. via `GOOGLE_APPLICATION_CREDENTIALS` or `gcloud auth activate-service-account`).

Parameters available in 'gs':

| Config key | Purpose |
|------------|---------|
| bucket | GCS bucket name. |
| gcs_creds_path | Path to the GCP service account JSON key file. |
| retention_copies | How many copies of older backups to keep. |
| retention_days | How many days of backups to keep. |


Destination - Samba
-------------------

You can specify a Samba share to back up to.

```json
{
  "id": "bigshare",
  "type": "samba",
  "host": "server1.local.lan",
  "share": "TheShare",
  "workgroup": "WORKGROUP",
  "credentials": {
    "username": "backups",
    "password": "getyourown"
  },
  "suffix": "gpg"
}
```

A temporary authentication credentials file will be created and the 'smbclient' client will be instructed to use it.

Parameters available in 'samba':

| Config key | Purpose |
|------------|---------|
| host | Samba (DNS) hostname. |
| share | Samba share to manage dump files on |
| username | Samba username. |
| password | Samba password. |
| workgroup | Samba domain/workgroup. |
| suffix | Suffix for created files. |


Destination - Local Filesystem
------------------------------

You can specify a local filesystem path to copy backups to. This is useful for writing to a mounted NFS share, USB drive, or any other locally accessible storage.

```json
{
  "id": "local-backup",
  "type": "local",
  "path": "/mnt/backup-drive",
  "retention_copies": 7
}
```

Parameters available in 'local':

| Config key | Purpose |
|------------|---------|
| path | Local filesystem path to copy backups to. |
| retention_copies | How many timestamped backup directories to keep. |
| retention_days | How many days of backups to keep. |


Destination - Backblaze B2
--------------------------

You can specify a Backblaze B2 bucket to back up to using the native B2 SDK.

```json
{
  "id": "b2-backup",
  "type": "b2",
  "bucket": "my-backup-bucket",
  "credentials": {
    "application_key_id": "your-application-key-id",
    "application_key": "your-application-key"
  },
  "retention_copies": 5,
  "retention_days": 30
}
```

Create an application key at https://secure.backblaze.com/app_keys.htm with read/write access to the target bucket.

Parameters available in 'b2':

| Config key | Purpose |
|------------|---------|
| bucket | B2 bucket name. |
| credentials.application_key_id | B2 application key ID. |
| credentials.application_key | B2 application key. |
| retention_copies | How many copies of older backups to keep. |
| retention_days | How many days of backups to keep. |


Destination - Minio / S3-Compatible
-------------------------------------

You can specify a Minio bucket (or any S3-compatible service such as DigitalOcean Spaces) to back up to using the native Minio SDK.

```json
{
  "id": "minio-backup",
  "type": "minio",
  "endpoint": "nyc3.digitaloceanspaces.com",
  "bucket": "my-backup-bucket",
  "secure": true,
  "credentials": {
    "access_key": "your-access-key",
    "secret_key": "your-secret-key"
  },
  "retention_copies": 5
}
```

For a local Minio instance, set `"secure": false` and use the host:port as the endpoint (e.g. `"localhost:9000"`).

Parameters available in 'minio':

| Config key | Purpose |
|------------|---------|
| endpoint | Minio/S3-compatible endpoint (host or host:port, no scheme). |
| bucket | Bucket name. |
| secure | Whether to use TLS (default: `true`). |
| credentials.access_key | Access key. |
| credentials.secret_key | Secret key. |
| retention_copies | How many copies of older backups to keep. |
| retention_days | How many days of backups to keep. |


Destination - Dropbox
---------------------

You can specify a Dropbox folder to back up to using the official Dropbox SDK.

```json
{
  "id": "dropbox-backup",
  "type": "dropbox",
  "access_token": "your-long-lived-access-token",
  "folder": "/backups",
  "retention_copies": 7
}
```

Generate a long-lived access token from https://www.dropbox.com/developers/apps.

Parameters available in 'dropbox':

| Config key | Purpose |
|------------|---------|
| access_token | Dropbox long-lived access token. |
| folder | Root folder path within Dropbox (default: `/backups`). |
| retention_copies | How many timestamped backup directories to keep. |


Destination - Google Drive
--------------------------

You can specify a Google Drive folder to back up to using a service account and `google-api-python-client`.

```json
{
  "id": "gdrive-backup",
  "type": "gdrive",
  "creds_file": "/etc/backups/gdrive-service-account.json",
  "folder_id": "your-google-drive-folder-id",
  "retention_copies": 10
}
```

To set up:
1. Create a service account at https://console.cloud.google.com
2. Enable the Google Drive API for the project
3. Download the JSON key file and place it on the backup host
4. Share the target Drive folder with the service account email address (with Editor permission)
5. Use the folder ID from the Drive URL as `folder_id`

Parameters available in 'gdrive':

| Config key | Purpose |
|------------|---------|
| creds_file | Path to the service account JSON key file. |
| folder_id | Google Drive folder ID to store backups in. |
| retention_copies | How many timestamped backup directories to keep. |
| retention_days | How many days of backups to keep. |


Notification - Email
--------------------

You can specify the SMTP configuration for notifications.

```json
{
  "host": "smtp.mycompany.com",
  "port": 587,
  "credentials": {}
    "username": "backups",
    "password": "relaypassword"
  },
  "use_tls": 1,
  "use_ssl": 0,
  "success_to": "archive@mycompany.com",
  "failure_to": "sysadmin@mycompany.com",
}
```

Parameters available in 'smtp':

| Config key | Purpose |
|------------|---------|
| host | SMTP hostname. |
| port | SMTP port. |
| username | SMTP username. |
| password | SMTP password. |
| use_tls | If using STARTTLS, '1'. |
| use_ssl | If using plain SSL, '1'. |
| success_to | If set, success notification will be sent to the address specified. If not set, success notification will not be sent. |
| failure_to | If set, failure notification will be sent to the address specified. If not set, failure notification will not be sent. |


Notification - HipChat
----------------------

You can specify that a notification of success or failure (or just failure) is posted as a HipChat room notification by providing the HipChat API credentials.

```json
{
  "type": "hipchat",
  "url": "https://www.hipchat.com/...",
  "notify_on_success": 0,
  "notify_on_failure": 1
}
```

Parameters available in 'hipchat':

| Config key | Purpose |
|------------|---------|
| url | URL provided by Hipchat for v2 integration. |


Notification - Discord
----------------------

You can specify that a notification of success or failure (or just failure) is posted as a Discord channel notification by providing the Discord webhook URL.

```json
{
  "type": "discord",
  "url": "https://discordapp.com/api/webhooks/...",
  "notify_on_success": 0,
  "notify_on_failure": 1
}
```

Parameters available in 'discord':

| Config key | Purpose |
|------------|---------|
| url | Discord webhook URL. |


Notification - Matrix
--------------------

You can specify that a notification of success or failure (or just failure) is posted as a Matrix room notification by providing Matrix service details.

```json
{
  "type": "matrix",
  "url": "https://matrix.org",
  "access_token": "ALongStringOfCharacters",
  "room_id": "!roomidstringofchars@matrix.org",
  "notify_on_success": 0,
  "notify_on_failure": 1
}
```

Parameters available in 'matrix':

| Config key | Purpose |
|------------|---------|
| url | Matrix home server URL. |
| access_token | Pre-obtained access token. |
| room_id | Matrix room ID for notifications. |


Notification - Slack
--------------------

You can specify that a notification of success or failure (or just failure) is posted as a Slack channel notification by providing a Slack URL.

```json
{
  "type": "slack",
  "url": "https://hooks.slack.com/services/Z03JDZYT4/B03JEZGFG/jqWw4Zr5xPuArlZbbUexIaxP",
  "notify_on_success": 0,
  "notify_on_failure": 1
}
```

Parameters available in 'slack':

| Config key | Purpose |
|------------|---------|
| url | Slack integration URL. |


Notification - Telegram
--------------------

You can specify that a notification of success or failure (or just failure) is posted as Telegram message by providing an API token and chat id.

```json
{
  "type": "telegram",
  "api_token": "295432120:use_your_own_token_here",
  "chat_id": "38123456",
  "notify_on_success": 0,
  "notify_on_failure": 1
}
```

Parameters available in 'telegram':

| Config key | Purpose |
|------------|---------|
| api_token | Telegram API token |
| chat_id | Telegram Chat ID |


Notification - Flag file
------------------------

This simply updates a flag file in a specific location if the backup is successful.

```json
{
  "type": "flagfile",
  "flagfile": "/backups/gitdata.ok"
}
```

We use this on our backup agents in conjunction with a simple 'file_age_secs' script running via SNMP. The following line in the 'snmpd.conf' file allows us to poll how long ago the last known successful backup was run.

```
exec check_git_backups /usr/local/bin/file_age_secs /backups/gitdata.ok
```

We then configure our monitoring/alerting service, Icinga, to poll this value and alert is if it exceeds a certain time.

(for file_age_secs source see https://gist.github.com/rossigee/44b9287e95068ebb9ae1)

Parameters available in 'flagfile':

| Config key | Purpose |
|------------|---------|
| filename | Filename for file to create on successful backup completion. |


Notification - Prometheus
-------------------------

Pushes a few statistics regarding the backup to a Prometheus push gateway.

```json
{
  "type": "prometheus",
  "url": "http://pushgw:9091/",
  "credentials": {
    "username": "prometheus",
    "password": "yourpasswordhere"
  }
}
```

If the 'username and 'password' parameters are set, they are used to create the HTTP Basic Auth header for the connection.

Parameters available in 'prometheus':

| Config key | Purpose |
|------------|---------|
| url | URL of Prometheus push gateway (not inc '/metrics' part). |
| username | Push gateway auth username. |
| password | Push gateway auth password. |

Notification - Elasticsearch
----------------------------

You can specify a configuration to store backup statistics as an entry in an Elasticsearch index.

```json
{
  "id": "logging",
  "type": "elasticsearch",
  "url": "https://logging-es-http.elasticsearch:9200",
  "credentials": {
    "username": "backups",
    "password": "yourpasswordhere"
  },
  "indexpattern": "backups-%Y"
}
```

Parameters available in 'elasticsearch':

| Config key | Purpose |
|------------|---------|
| url | Elasticsearch URL, including authentication if required |
| indexpattern | Pattern to use to determine the index to store the document to. |


Complete Example
----------------

This simple example backs up some folders and a database, and deposits them to a Samba share, notifying sysadmin on failure only.

```json
{
  "tmpdir": "/var/tmp/folderdumps",
  "modules": [
    "backups.sources.folder",
    "backups.sources.mysql",
    "backups.destinations.s3",
    "backups.notifications.smtp"
  ],
  "sources": [
    {
      "id": "config",
      "type": "folder",
      "name": "Live server config",
      "path": "/etc",
      "passphrase": "youllneverguesswhat"
    },
    {
      "id": "data",
      "type": "folder",
      "name": "Live server data folder",
      "path": "/data",
      "passphrase": "youllneverguesswhat"
    },
    {
      "id": "db",
      "type": "mysql",
      "name": "Live server database",
      "path": "/data",
      "passphrase": "youllneverguesswhat"
    },
  ],
  "destinations": [
    {
      "id": "myamazon",
      "type": "s3",
      "bucket": "mybucketnamehere",
      "region": "eu-west-1",
      "credentials": {
        "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
        "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY"
      }
    }
  ],
  "notifications": []
}
```




Credits
-------

Ross Golder <ross@golder.org>
