# Scheduling Backups

## Using systemd timers (recommended)

systemd timers are the recommended way to schedule backups on modern Linux systems. They provide better logging, dependency management, and monitoring than cron.

### Service unit

Create `/etc/systemd/system/backups@.service`:

```ini
[Unit]
Description=Run backup job %i
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backups /etc/backups/%i.json
User=root
StandardOutput=journal
StandardError=journal
SyslogIdentifier=backups-%i
```

### Timer unit

Create `/etc/systemd/system/backups@.timer`:

```ini
[Unit]
Description=Scheduled backup job %i

[Timer]
OnCalendar=*-*-* 03:00:00
RandomizedDelaySec=300
Persistent=true

[Install]
WantedBy=timers.target
```

### Enable and start

```bash
# Enable and start a timer for a specific config file (e.g. /etc/backups/production.json)
systemctl enable --now backups@production.timer

# Check status
systemctl status backups@production.timer
systemctl status backups@production.service

# View logs
journalctl -u backups@production.service -f
```

The `@` (template) unit lets you run multiple backup jobs from one pair of unit files, one per config file.

### Per-job timers

If you need different schedules per job, create separate timer overrides:

```bash
systemctl edit backups@offsite.timer
```

```ini
[Timer]
OnCalendar=
OnCalendar=*-*-* 01:00:00
```

## Using cron

Add an entry to `/etc/cron.d/backups`:

```cron
# Run backups daily at 3am
0 3 * * * root /usr/local/bin/backups /etc/backups/production.json >> /var/log/backups.log 2>&1
```

Or using `crontab -e` for the root user:

```cron
0 3 * * * /usr/local/bin/backups /etc/backups/production.json
```

## Monitoring

Pair the backup job with the [flag file notification](notifications/flagfile.md) for simple freshness monitoring, or the [Prometheus notification](notifications/prometheus.md) for metrics-based alerting.
