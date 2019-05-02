# Using this with Docker

See the example `Dockerfile` in this repo.

An example notify script...

```
#!/bin/sh

curl -X POST -H "Content-Type: application/json" -d @- $WEBHOOK_URL
```

You need to mount a simple 'jobber.conf' schedule file into the container as `/root/.jobber`. An example Jobber config:

```
[prefs]
  notifyProgram: /notify-webhook.sh

[jobs]
- name: MasterDBBackup
  cmd: backup -v /backups-conf/masterdb.json
  time: 0 30 0
  onError: Stop
  notifyOnError: true
  notifyOnFailure: true

```

Obviously, you also need to mount the configuration file the backup script uses, and any volumes it will need access to to back up.

