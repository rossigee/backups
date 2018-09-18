# Using this with Docker

Here's an example:

```
FROM alpine:latest

# Install main O/S applications required
RUN apk add --no-cache \
        curl git rsync vim sudo \
        python py-mysqldb py-pip \
	mariadb-client \
        postgresql-client postgresql \
	gnupg \
	zip unzip \
        supervisor

# Install Jobber app binary for scheduling
RUN curl -sLO https://github.com/dshearer/jobber/releases/download/v1.3.2/jobber-1.3.2-r0_alpine3.6and3.7.apk && \
	apk add --allow-untrusted jobber-1.3.2-r0_alpine3.6and3.7.apk; \
	rm -f jobber-1.3.2-r0_alpine3.6and3.7.apk

# Install main python packages required
RUN pip install \
	git+https://github.com/rossigee/backups \
	awscli \
	boto \
	prometheus_client

# Set up our custom notification handler
ADD /notify-webhook.sh /notify-webhook.sh
RUN chmod 755 /notify-webhook.sh

# Run the scheduler
CMD ["/usr/libexec/jobbermaster"]

```

(and the notify script just...)

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

