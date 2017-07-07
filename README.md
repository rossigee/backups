- [ ] Backup scripts
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
* a Samba share (uses pysmbc)

Currently implemented notifications are:

* an e-mail (via smtplib)
* a HipChat room notification
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

For flexibility, configuration variables are read first from environment variables, and can be overridden by settings in the configuration file provided at runtime. The configuration file location is specified as a command line argument, so different configurations can be run at different times on the same backup server, for different data at different times.

The configuration file may contain a 'defaults' block that defines various values that are shared by, or not specific to a particular source, destination or notification. Where specified, these will override the environment variable for that setting.

```
[defaults]
hostname=my.hostname.com
tmpdir=/var/tmp/backups
passphrase=9a3d2ad085cd1fff0f43501a84e7913d
```

Parameters available in 'defaults':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| hostname | BACKUPS_HOSTNAME | Used to help identify the folder the backup should be stored in on the destination. |
| tmpdir | BACKUPS_TMPDIR | Somewhere with enough temporary space to contain the compressed backup and it's encrypted copy as it's being built. |
| passphrase| BACKUPS_PASSPHRASE | Used to encrpyt any backups created. |

These values can be overridden in the source configuration blocks.

The rest of the configuration file will consist of blocks defining the various sources, destination and notification handlers.


Source - Folder
---------------

You can specify one or more folders to be backed up.

```
[folder-accountsdata]
name=Live Accounts Data
path=/var/lib/myaccountspkg/data

[folder-devsdata]
name=Live Development Data
path=/var/lib/mydevteamfiles/data

```

You can specify multiple 'exclude' parameters to tell tar which folders/files to exclude too.

```
[folder-websitedata]
name=Live Website Data
path=/var/www/htdocs
exclude=logs
exclude=tmp
```

Parameters available in 'folder':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| name | N/A | Description of data being backed up (for reporting purposes). |
| path | N/A | Name of file or folder to be backed up. |
| exclude | N/A | One or more paths to be excluded from the backup |


Source - MySQL Database
-----------------------

You can specify one of more mySQL databases to be backed up.

```
[mysql-livesupportdb]
name=Live Company Data
dbhost=localhost
dbname=livecompanydb
dbuser=backups
dbpass=zzzuserwithreadonlyperms
passphrase="your-devs-will-know-this"
```

The script creates a temporary 'mysqlclient' credentials file using the given details.

By default, the '--events' flag is passed to mysqldump. This may break older versions of mysqldump (prior to version 5.1, IIRC), so you can disable this flag with the 'noevents' parameter.

```
[client]
host=specific.host.database.com
...
noevents=1
```

Parameters available in 'mysql':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| name | N/A | Description of data being backed up (for reporting purposes). |
| dbhost | MYSQL_HOST | Name of the mySQL host to connect to. |
| dbname | N/A | Name of the mySQL database to back up. |
| dbuser | MYSQL_USER | Username to connect to mySQL as. |
| dbpass | MYSQL_PASS | Password to connect to mySQL with. |
| defaults | N/A | The location of an 'mysqlclient' credentials file to use instead of creating a temporary one with using above 'db*' variables. |
| noevents | N/A | Don't pass the '--events' flag to 'mysqldump'. |


Source - PostgreSQL Database
----------------------------

You can specify one of more PostgreSQL databases to be backed up.

```
[pgsql-livesupportdb]
name=Live Company Data
dbhost=localhost
dbname=livecompanydb
dbuser=backups
dbpass=zzzuserwithreadonlyperms
passphrase="your-devs-will-know-this"
```

The script creates a temporary 'pgpass' credentials file using the given details.

```
[client]
host=specific.host.database.com
...
noevents=1
```

Parameters available in 'mysql':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| name | N/A | Description of data being backed up (for reporting purposes). |
| dbhost | PGSQL_HOST | Name of the PostgreSQL host to connect to. |
| dbname | N/A | Name of the PostgreSQL database to back up. |
| dbuser | PGSQL_USER | Username to connect to PostgreSQL as. |
| dbpass | PGSQL_PASS | Password to connect to PostgreSQL with. |


Source - RDS Database Snapshots
-----------------------

You can specify one or more RDS databases to be backed up, where they have automated rolling backups enabled.

The last automatic snapshot of the given database will be identified using the AWS credentials provided. That will then be restored to a temporary instance, in a security group that allows access to the agent machine. The agent machine (running this script), will then 'mysqldump' the data to a '.sql.gz' file, and destroy the temporary instance.

WARNING: This can take a very long time in many cases.

```
[rds-livesupportdb]
name=Live Company Data
dbhost=localhost
dbname=livecompanydb
dbuser=backups
dbpass=zzzuserwithreadonlyperms
instancename=livedb1
region=eu-west-1
security_group=livedbbackup
instance_class=db.m1.small
defaults=/home/backups/mysql-livedb.conf

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

The 'mysqlclient' gets it's host, username and password from the 'backups' user's '~/.my.cnf' file. This need to be configured:

```
# cat >/home/backups/.my.cnf <<EOF
[client]
host=typically.localhost
user=backups
password=mybackuppassword
EOF
# chown backups /home/backups/.my.cnf
# chmod 400 /home/backups/.my.cnf
```

You can specify an alternative, per-source MySQL 'defaults' file, containing individual credentials for each one, using the 'defaults' parameter. This parameter is used for the '--defaults-file' argument to mysqldump.

```
[client]
host=specific.host.database.com
...
defaults=/etc/backups/mysql-specific.conf
```

By default, the '--events' flag is passed to mysqldump. This may break older versions of mysqldump (prior to version 5.1, IIRC), so you can disable this flag with the 'noevents' parameter.

```
[client]
host=specific.host.database.com
...
noevents=1
```

The 'security_group' must allow access from the host running mysqldump.

Parameters available in 'rds':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| name | N/A | Description of data being backed up (for reporting purposes). |
| dbhost | MYSQL_HOST | Name of the mySQL host to connect to. |
| dbname | N/A | Name of the mySQL database to back up. |
| dbuser | MYSQL_USER | Username to connect to mySQL as. |
| dbpass | MYSQL_PASS | Password to connect to mySQL with. |
| defaults | N/A | The location of an 'mysqlclient' credentials file to use instead of creating a temporary one with using above 'db*' variables. |
| noevents | N/A | Don't pass the '--events' flag to 'mysqldump'. |
| aws_access_key_id | AWS_ACCESS_KEY_ID | AWS access key |
| aws_secret_access_key | AWS_SECRET_ACCESS_KEY | AWS secret access key |
| instancename | N/A | RDS instance name to clone backup of. |
| region | N/A | AWS hosting region of RDS database. |
| security_group | N/A | VPC security group for replica to provide access to. |
| instance_class | N/A | RDS instance class to create replica as (defaults to 'db.m1.small'). |


Source - PostgreSQL
-------------------

Patches/pull requests welcome here!

For now, I am just backing up the data on the filesystem using a 'folder' source, but it has a very low transaction volume, so it's not likely to be an issue.


Source - Volume snapshots
-------------------------

This method allows us to specify a set of RDS/EC2 volumes. When sourced, this plugin which issue snapshot commands to the volumes specified.

```
[defaults]
aws_access_key_id=...
aws_secret_access_key=...

[snapshot-rds-mainrdsdb]
availability_zone=eu-west-1
volume_id=mainrds

[snapshot-ec2-mailfolders]
availability_zone=eu-west-1
volume_id=vol-81dc59c6

[snapshot-ec2-mailfolders]
availability_zone=eu-west-1
volume_id=vol-81dc59c6

```

It leaves a temporary file with status details as a 'dumpfile'. This gives the destination plugin something to work with when reporting success.

This source plugin is best used in a configuration on it's own, or with other volume snapshot definitions only, as used with a destination but no payload the configuration wouldn't make much sense!

Parameters available in 'snapshot':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| name | N/A | Description of data being backed up (for reporting purposes). |
| volume_id | N/A | ID of the EBS volume to be snapshotted. |
| availability_zone | AWS_AVAILABILITY_ZONE | AWS availability zone. |
| aws_access_key_id | AWS_ACCESS_KEY_ID | AWS access key. |
| aws_secret_access_key | AWS_SECRET_ACCESS_KEY | AWS secret access key. |


Destination - S3
----------------

You can specify an S3 bucket to back up to.

```
[s3-backups]
bucket=backups-123456789
```

The 'aws' CLI client gets it's authentication credentials and other configuration from the 'backups' user's '~/.aws/config' file. This needs to be configured as per instructions in the AWS CLI documentation.

Additionally, the S3 destination provides some simple backup rotation options.

```
[s3-backups]
bucket=backups-123456789
prefix=gnucash
availability_zone=eu-west-1
aws_access_key_id=AKIAJPG7RJVVKWT3UX3A
aws_secret_access_key=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
retention_copies=10
#retention_days=90
```

After a successful backup, the backup files are listed and the 'retention_copies' and 'retention_days' options, if present, are applied to identify and remove any backups that are no longer required.

Parameters available in 's3':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| bucket | N/A | S3 bucket to dump files to. |
| availability_zone | AWS_AVAILABILITY_ZONE | AWS availability zone. |
| aws_access_key_id | AWS_ACCESS_KEY_ID | AWS access key. |
| aws_secret_access_key | AWS_SECRET_ACCESS_KEY | AWS secret access key. |
| retention_copies | RETENTION_COPIES | How many copies of older backups to keep. |
| retention_days | RETENTION_DAYS | How many days of backups to keep. |


Destination - Samba
-------------------

You can specify a Samba share to back up to.

```
[samba-backups]
hostname=qnap.mycompany.com
share=Backups
username=backups
password=getyourown
workgroup=WORKGROUP
```

A temporary authentication credentials file will be created and the 'smbclient' client will be instructed to use it.

Parameters available in 'samba':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| hostname | SMB_HOSTNAME | Samba (DNS) hostname. |
| share | N/A | Samba share to manage dump files on |
| username | SMB_USERNAME | Samba username. |
| password | SMB_PASSWORD | Samba password. |
| workgroup | SMB_WORKGROUP | Samba domain/workgroup. |


Notification - Email
--------------------

You can specify the SMTP configuration for notifications.

```
[smtp]
host=smtp.mycompany.com
port=587
username=backups
password=relaypassword
use_tls=1
use_ssl=0
success_to=archive@mycompany.com
failure_to=sysadmin@mycompany.com
```

Parameters available in 'smtp':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| host | SMTP_HOST | SMTP hostname. |
| port | SMTP_PORT | SMTP port. |
| username | SMTP_USERNAME | SMTP username. |
| password | SMTP_PASSWORD | SMTP password. |
| use_tls | SMTP_USE_TLS | If using STARTTLS, '1'. |
| use_ssl | SMTP_USE_SSL | If using plain SSL, '1'. |
| success_to | SMTP_SUCCESS_TO | If set, success notification will be sent to the address specified. If not set, success notification will not be sent. |
| failure_to | SMTP_FAILURE_TO | If set, failure notification will be sent to the address specified. If not set, failure notification will not be sent. |


Notification - HipChat
----------------------

You can specify that a notification of success or failure (or just failure) is posted as a HipChat room notification by providing the HipChat API credentials.

```
[hipchat]
url=https://www.hipchat.com/...
notify_on_success=False
notify_on_failure=True
```

Parameters available in 'hipchat':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| url | HIPCHAT_URL | URL provided by Hipchat for v2 integration. |


Notification - Slack
--------------------

You can specify that a notification of success or failure (or just failure) is posted as a Slack channel notification by providing a Slack URL.

```
[slack]
url=https://hooks.slack.com/services/Z03JDZYT4/B03JEZGFG/jqWw4Zr5xPuArlZbbUexIaxP
notify_on_success=False
notify_on_failure=True
```

Parameters available in 'slack':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| url | SLACK_URL | Slack integration URL. |


Notification - Telegram
--------------------

You can specify that a notification of success or failure (or just failure) is posted as Telegram message by providing an API token and chat id.

```
[telegram]
api_token=295432120:use_your_own_token_here
chat_id=38123456
notify_on_success=True
notify_on_false=True
```

Parameters available in 'telegram':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| api_token | TELEGRAM_API_TOKEN | Telegram API token |
| chat_id | TELEGRAM_CHAT_ID | Telegram Chat ID |


Notification - Flag file
------------------------

This simply updates a flag file in a specific location if the backup is successful.

```
[flagfile]
filename=/backups/gitdata.ok
```

We use this on our backup agents in conjunction with a simple 'file_age_secs' script running via SNMP. The following line in the 'snmpd.conf' file allows us to poll how long ago the last known successful backup was run.

```
exec check_git_backups /usr/local/bin/file_age_secs /backups/gitdata.ok
```

We then configure our monitoring/alerting service, Icinga, to poll this value and alert is if it exceeds a certain time.

(for file_age_secs source see https://gist.github.com/rossigee/44b9287e95068ebb9ae1)

Parameters available in 'flagfile':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| filename | N/A | Filename for file to create on successful backup completion. |


Notification - Prometheus
-------------------------

Pushes a few statistics regarding the backup to a Prometheus push gateway.

```
[prometheus]
url=http://pushgw:9091/
username=prometheus
password=yourpasswordhere

```

If the 'username and 'password' parameters are set, they are used to create the HTTP Basic Auth header for the connection.

Parameters available in 'prometheus':

| Config key | Environment variable | Purpose |
|------------|----------------------|---------|
| url | PUSHGW_URL | URL of Prometheus push gateway (not inc '/metrics' part). |
| username | PUSHGW_USERNAME | Push gateway auth username. |
| password | PUSHGW_PASSWORD | Push gateway auth password. |

Complete Example
----------------

This simple example backs up some folders and a database, and deposits them to a Samba share, notifying sysadmin on failure only.

```
[defaults]
hostname=myserver.mycompany.com
passphrase=64b0c7405f2d8051e2b9f02aa4898acc
tmpdir = /var/tmp/folderdumps

[folder-etc]
path=/etc

[folder-data]
path=/var/lib/app/data

[mysql-companyapp]
dbname=companyapp

[s3]
bucket=backups-1234567

[smtp]
failure_to=you@mycompany.com

```


Credits
-------

Ross Golder <ross@golder.org>
