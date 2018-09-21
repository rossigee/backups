Backup scripts
==============

This python script, given a backup configuration, will cycle through a list of backup 'sources', packing them up and encrypting them into a temporary file, which it will upload to each of a list of destinations, finally reporting success or failure via a list of notification handlers.

Overview
--------

Roughly speaking there are 'sources', 'destinations' and 'notifications'.

Currently implemented sources are:

* folders (using tar)
* MySQL databases (using mysqldump).
* RDS database snapshots (using mysqldump).
* PostgreSQL databases (using pg_dump).

Currently implemented destinations are:

* an S3 bucket (uses aws-cli)
* an GS bucket (uses gsutil)
* a Samba share (uses pysmbc)

Currently implemented notifications are:

* an e-mail (via smtplib)
* a HipChat room notification
* a Discord room notification
* a Slack notification
* a Telegram notification
* a simple flag file
* a Prometheus push gateway

Hopefully, it's fairly straightforward to extend or add to the above.

The sources will be used to generate dump files in a temporary working area. By default, this is '/var/tmp', but for large DB dumps, you may need to specify an alternative folder mounted somewhere with enough space to store a compressed dump, and it's encrypted equivalent, temporarily.

Backups will be encrypted with a given passphrase (using GnuPG), and put into a folder on the destination using the following filename pattern...

    /{hostname}/{yyyy-mm-dd}/{dumpfile_id}.{sql|tar}.gpg

If the backup configuration specifies a retention policy, then any copies that exist on the backup destination that fall outside that scope are deleted. Typically, a retention policy will specify to keep a copies for a certain number of days, or just a number of the most recent copies.

Also, a word to the wise about scheduling. Backing up large chunks of data can use a lot of resources, and even if set to run after 'work' hours, can often run for on into the morning and indeed the next working day. Break larger backups down into smaller chunks where possible. If you are backing up mission criticial servers over mission critical network connections, you may need to take additional precautions to ensure that your backup scripts are not going to cause knock-on problems. You have been warned.

For security purposes, the script is designed to run as a non-privileged user. By default, it expects to be run as the 'backups' user, but this can be overridden using the 'RUN_AS_USER' environment variable.


Installation
------------

1. Install me. Unpack me, run 'python setup.py' as root.

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
| passphrase | A passphrase to encrypt the backup with (using GnuPG). |
| excludes | One or more files/paths to be excluded from the backup. |


Source - MySQL Database
-----------------------

You can specify one of more mySQL databases to be backed up.

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
  "passphrase": "64b0c7405f2d8051e2b9f02aa4898acc"
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

Parameters available in 'mysql':

| Config key | Purpose |
|------------|---------|
| name | Description of data being backed up (for reporting purposes). |
| dbhost | Name of the mySQL host to connect to. |
| dbname | Name of the mySQL database to back up. |
| dbuser | Username to connect to mySQL as. |
| dbpass | Password to connect to mySQL with. |
| defaults | The location of an 'mysqlclient' credentials file to use instead of creating a temporary one with using above 'db*' variables. |
| directives | An optional string of options to pass to 'mysqldump'. |
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


Source - RDS Database Snapshots
-----------------------

You can specify one or more Amazon RDS databases to be backed up, where they have automated rolling backups enabled. Currently, this only supports MySQL-based RDS instances.

The last automatic snapshot of the given database will be identified using the AWS credentials provided. That will then be restored to a temporary instance, in a security group that allows access to the agent machine. The agent machine (running this script), will then 'mysqldump' the data to a '.sql.gz' file, and destroy the temporary instance. This avoids the need to run any backup queries that would adversely affect the performance of the live database.

WARNING: This can take a very long time in many cases.

```json
{
  "id": "livecompanydb",
  "name": "Live Company Data",
  "type": "pgsql",
  "dbhost": "localhost",
  "dbname": "livecompany",
  "dbuser": "backups",
  "dbpass": "zzzuserwithreadonlyperms",
  "instancename": "livedb1",
  "region": "eu-west-1",
  "security_group": "livedbbackup",
  "instance_class": "db.m1.small",
  "passphrase": "64b0c7405f2d8051e2b9f02aa4898acc"
}
```

This module uses the 'boto' package, and expects auth credentials to be provided in the '~/.boto' file. This needs to be configured:

```
# cat >/home/backups/.boto <<EOF
[Credentials]
aws_access_key_id = YOURACCESSKEY
aws_secret_access_key = YOURSECRETKEY
EOF
# chown backups /home/backups/.boto
# chmod 400 /home/backups/.boto
```

By default, the '--events' flag is passed to mysqldump. This may break older versions of mysqldump (prior to version 5.1, IIRC), so you can disable this flag with the 'noevents' parameter.

The 'security_group' must allow access from the host running mysqldump.

Parameters available in 'rds':

| Config key | Purpose |
|------------|---------|
| name | Description of data being backed up (for reporting purposes). |
| dbhost | Name of the mySQL host to connect to. |
| dbname | Name of the mySQL database to back up. |
| dbuser | Username to connect to mySQL as. |
| dbpass | Password to connect to mySQL with. |
| defaults | The location of an 'mysqlclient' credentials file to use instead of creating a temporary one with using above 'db*' variables. |
| noevents | Don't pass the '--events' flag to 'mysqldump'. |
| aws_access_key_id | AWS access key |
| aws_secret_access_key | AWS secret access key |
| instancename | RDS instance name to clone backup of. |
| region | AWS hosting region of RDS database. |
| security_group | VPC security group for replica to provide access to. |
| instance_class | RDS instance class to create replica as (defaults to 'db.m1.small'). |


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
    "aws_access_key_id": "AKIAJPG7RJVVKWT3UX3A",
    "aws_secret_access_key": "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"
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


Destination - S3
----------------

You can specify an S3 bucket to back up to.

```json
{
  "bucket": "backups-123456789",
}
```

The 'aws' CLI client gets it's authentication credentials and other configuration from the 'backups' user's '~/.aws/config' file. This needs to be configured as per instructions in the AWS CLI documentation.

Additionally, the S3 destination provides some simple backup rotation options. After a successful backup, the backup files are listed and the 'retention_copies' and 'retention_days' options, if present, are applied to identify and remove any backups that are no longer required.

Parameters available in 's3':

| Config key | Purpose |
|------------|---------|
| bucket | S3 bucket to dump files to. |
| region | AWS availability zone. |
| aws_access_key_id | AWS access key. |
| aws_secret_access_key | AWS secret access key. |
| retention_copies | How many copies of older backups to keep. |
| retention_days |  How many days of backups to keep. |


Destination - GS
----------------

You can specify a GS bucket to back up to.

```json
{
  "bucket": "backups-123456789",
}
```

The 'gsutil' CLI client gets it's authentication credentials and other configuration from the 'backups' user's '~/.boto' file. 
The GS module requires a GCP service account to be created with appropriate permissions to write and delete from GS buckets. The key file needs to be in P12 format. Properly secure this file and related information.

```
[Credentials]
gs_service_client_id = some-service-account@your-project.iam.gserviceaccount.com
gs_service_key_file = /some/path/to/your/service-account-credential-file.p12
gs_service_key_file_password = asecretpassword

[GSUtil]
default_api_version = 2
```

Additionally, the GS destination provides some simple backup rotation options. After a successful backup, the backup files are listed and the 'retention_copies' and 'retention_days' options, if present, are applied to identify and remove any backups that are no longer required.

Parameters available in 's3':

| Config key | Purpose |
|------------|---------|
| bucket | GS bucket to dump files to. |
| gs_service_client_id | GCP service account. |
| gs_service_key_file | Location of service account file. |
| gs_service_key_file_password | Password for service account file (in P12 format). |
| retention_copies | How many copies of older backups to keep. |
| retention_days |  How many days of backups to keep. |


Destination - Samba
-------------------

You can specify a Samba share to back up to.

```json
{
  "id": "bigshare",
  "type": "samba",
  "hostname": "server1.local.lan",
  "share": "TheShare",
  "workgroup": "WORKGROUP",
  "credentials": {
    "username": "backups",
    "password": "getyourown"
  }
}
```

A temporary authentication credentials file will be created and the 'smbclient' client will be instructed to use it.

Parameters available in 'samba':

| Config key | Purpose |
|------------|---------|
| hostname | Samba (DNS) hostname. |
| share | Samba share to manage dump files on |
| username | Samba username. |
| password | Samba password. |
| workgroup | Samba domain/workgroup. |


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
        "aws_access_key_id": "AKIAJPG7RJVVKWT3UX3A",
        "aws_secret_access_key": "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"
      }
    }
  ],
  "notifications": []
}
```


Credits
-------

Ross Golder <ross@golder.org>
