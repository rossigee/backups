Backup scripts
==============

At first, there was the shell script. It was good, but then things got complicated. Born from the ensuing chaos and spaghetti was the python package.

Overview
--------

Roughly speaking there are 'sources', 'destinations' and 'notifications'.

Currently implemented sources are:

* folders (using tar)
* databases (using mysqldump).

Currently implemented destinations are:

* an S3 bucket (s3cmd)
* a Swift container (swift-client)
* a Samba share (pysmbc)

Currently implemented notifications are:

* an e-mail (via SMTP)
* a HipChat room notification

Hopefully, it's fairly straightforward to extend or add to the above.

The sources will be used to generate dump files in a temporary working area. By default, this is '/var/tmp', but for large DB dumps, you may need to specify an alternative folder mounted somewhere with enough space to store a compressed dump, and it's encrypted equivalent, temporarily.

Backups will be encrypted with a given passphrase (using GnuPG), and put into a folder on the destination using the following filename pattern...

    /{hostname}/{yyyy-mm-dd}/{dumpfile_id}.{sql|tar}.gz.gpg

There is currently no provision for automatic housekeeping. For now, I manually remove older backups from time to time, leaving one or two for those moments that may require a tardis.

Also, a word to the wise about scheduling. Backing up large chunks of data can use a lot of resources, and even if set to run after 'work' hours, can often run for on into the morning and indeed the next working day. If you are backing up mission criticial servers over mission critical network connections, you may need to take additional precautions to ensure that your backup scripts are not going to cause knock-on problems. You have been warned.


Installation
------------

1. Install me. Unpack me, run 'python setup.py' as root.

1. Create a configuration file listing the folders/databases you want to back up, an encryption passphrase, and one or more places you want the encrypted dump file uploaded to, and details of any notification methods you wish to use. See docs further down for examples. You can install the dependencies now, or you can wait until you get errors later :)

1. Create a 'backups' user, and add a cron job to run the script as you wish. If you need folders to be backed up, you will also need a 'sudoers' directive to allow the backups user to run 'tar' as root to do it's work.

```
# cat >/etc/sudoers.d/99-backups <<EOF
backups ALL=(ALL) NOPASSWD: /bin/tar
EOF
```

1. Test your configuration by doing an initial run of the backup.

``` bash
# sudo -H -u backups /usr/local/bin/backup -v /home/backups/mynightlybackup.cfg
```

1. Add it to cron.

```
# cat >/etc/cron.d/nightly-backups.conf <<EOF
0 2 * * * backups /usr/local/bin/backup /home/backups/mynightlybackup.cfg
EOF
```

You're done.


Example configuration
---------------------

IMPORTANT: This configuration file will contain sensitive information. Be sure to keep it somewhere safe, with suitable permissions.

No assumptions are made as to where to store the configuration file. It is specified as a command line argument, so different configurations can be run at different times on the same server, for flexibity. In most cases, there is only one config file per server, and I tend to just use '/etc/backups.cfg'.

The configuration file needs to contain a common configuration block that defines the bits that are not specific to a particular source, destination or notification.

```
[defaults]
hostname=my.hostname.com
tmpdir=/var/tmp/backups
passphrase=9a3d2ad085cd1fff0f43501a84e7913d
```

The 'host' parameter is used to identify the folder the backup should be stored in on the destination.

The 'tmpdir' parameter is somewhere with enough temporary space to contain the compressed backup and it's encrypted copy as it's being built. I find it's best to create a subfolder of /var/tmp that only the 'backups' user has access to.

The 'passphrase' parameter is used to encrpyt any backups created. It can also be supplied in a source block to provide per-dump encryption passphrases, which may be useful if different dumps will need to be made accessible to different groups of users, such as developers that may need to download a fresh snapshot to use for local testing at various times. Depending on your circumstances, you may prefer the passphrase to be human-rememberable. In my case I don't, so I tend to use long randomly generated strings (i.e. openssl rand -hex 16).


Source - Folder
---------------

You can specify one or more folders to be backed up.

```
[folder-accountsdata]
path=/var/lib/myaccountspkg/data
passphrase="your-secret-is-safe-with-me"
```


Source - MySQL Database
-----------------------

You can specify one of more mySQL databases to be backed up.

```
[mysql-livesupportdb]
dbname=livecompanydb
passphrase="your-devs-will-know-this"
```

The 'mysqlclient' gets it's host, username and password from the 'backups' user's '~/.my.cnf' file. This need to be configured:

```
# cat >/home/backups/.my.cnf <<EOF
[client]
host=typically.localhost
user=thatsme
password=youguessit
EOF
# chown backups /home/backups/.my.cnf
# chmod 400 /home/backups/.my.cnf
```


Source - PostgreSQL
-------------------

Patches/pull requests welcome here!

For now, I am just backing up the data on the filesystem using a 'folder' source, but it has a very low transaction volume, so it's not likely to be an issue.


Destination - S3
----------------

You can specify an S3 bucket to back up to.

```
[s3-backups]
bucket=backups-123456789
```

The 's3cmd' client gets it's authentication credentials and other configuration from the 'backups' user's '~/.s3cfg' file. This needs to be configured.

```
# # Assumes you have a 's3cfg' file to hand. If not, create/find one!
# cp /tmp/example.s3cfg /home/backups/.s3cfg
# chown backups /home/backups/.s3cfg
# chmod 400 /home/backups/.s3cfg
```


Destination - Swift
-------------------

Actually, I lied. I haven't got this working or merged yet. Watch this space.


Destination - Samba
-------------------

You can specify a Samba share to back up to.

```
[samba-backups]
host=qnap.mycompany.com
workgroup=WORKGROUP
share=Backups
```

The 'smbclient' client is told to get it's configuration from the 'backups' user's '~/.smb.conf' file. This needs to be configured.

```
# cat >/home/backups/.smbauth <<EOF
username = backups
password = getyourown
domain = WORKGROUP
EOF
# chown backups /home/backups/.smbauth
# chmod 400 /home/backups/.smbauth
```


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

The main parameters ('host', 'port', 'user', 'password', 'use_tls' and 'use_ssl') should be fairly self-explanatory. They are optional. If no details are supplied, defaults to 'localhost' port 25.

The 'success_to' parameter is optional. Success notification will only be sent if it's supplied.

The 'failure_to' parameter is too, but then if you didn't supply it, how would you know if it worked or not?!


Notification - HipChat
----------------------

You can specify that a notification of success or failure (or just failure) is posted as a HipChat room notification by providing the HipChat API credentials.

```
[hipchat]
auth_token=01235456yougetthisfromhipchatadmin
room=Backups
notify_on_success=0
notify_on_failure=1
```


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

BTC: 1EN5wttKpwi2cdWMeUVQ4Wy15jBJZSBCDn

LTC: LejNzHEmWRZ76CY5Kwhzijjbv3X6Yk3Paw
