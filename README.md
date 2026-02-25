Backup scripts
==============

A Python backup orchestration tool. Given a JSON configuration file, it cycles through **sources** (databases, folders, cloud snapshots), compresses and optionally encrypts each backup, uploads to one or more **destinations**, and reports via **notifications**.

## Quick start

```bash
pip install backups
backups /etc/backups/production.json
```

See [docs/scheduling.md](docs/scheduling.md) for how to run as a systemd timer or cron job.

## Configuration

Configuration is a single JSON file:

```json
{
  "sources": [ ... ],
  "destinations": [ ... ],
  "notifications": [ ... ]
}
```

### Encryption (optional)

Add to the top level to encrypt backups before upload:

```json
{
  "encryption": {
    "type": "symmetric",
    "passphrase": "YOUR_PASSPHRASE"
  }
}
```

Or asymmetric (GPG public key):

```json
{
  "encryption": {
    "type": "asymmetric",
    "recipient": "ops@example.com"
  }
}
```

## Sources

| Type | Description | Docs |
|------|-------------|------|
| `folder` | Local directory via `tar` | [docs/sources/folder.md](docs/sources/folder.md) |
| `folder-ssh` | Remote directory via SSH + `tar` | [docs/sources/folderssh.md](docs/sources/folderssh.md) |
| `mysql` | MySQL/MariaDB via `mysqldump` | [docs/sources/mysql.md](docs/sources/mysql.md) |
| `mysql-ssh` | MySQL via SSH tunnel | [docs/sources/mysqlssh.md](docs/sources/mysqlssh.md) |
| `postgresql` | PostgreSQL via `pg_dump` | [docs/sources/postgresql.md](docs/sources/postgresql.md) |
| `rds` | AWS RDS MySQL snapshot | [docs/sources/rds.md](docs/sources/rds.md) |
| `rds-pgsql` | AWS RDS PostgreSQL snapshot | [docs/sources/rdspostgresql.md](docs/sources/rdspostgresql.md) |
| `snapshot` | Azure Managed Disk snapshot | [docs/sources/snapshot.md](docs/sources/snapshot.md) |
| `lvm-ssh` | LVM snapshot over SSH | [docs/sources/lvm-ssh.md](docs/sources/lvm-ssh.md) |

## Destinations

| Type | Description | Docs |
|------|-------------|------|
| `s3` | AWS S3 bucket | [docs/destinations/s3.md](docs/destinations/s3.md) |
| `gs` | Google Cloud Storage | [docs/destinations/gs.md](docs/destinations/gs.md) |
| `b2` | Backblaze B2 | [docs/destinations/b2.md](docs/destinations/b2.md) |
| `minio` | Minio / S3-compatible (DO Spaces, Wasabi, etc.) | [docs/destinations/minio.md](docs/destinations/minio.md) |
| `dropbox` | Dropbox | [docs/destinations/dropbox.md](docs/destinations/dropbox.md) |
| `gdrive` | Google Drive | [docs/destinations/gdrive.md](docs/destinations/gdrive.md) |
| `local` | Local filesystem path (NFS, USB, etc.) | [docs/destinations/local.md](docs/destinations/local.md) |
| `samba` | Samba/CIFS share | [docs/destinations/samba.md](docs/destinations/samba.md) |

All destinations support `retention_copies` and/or `retention_days` to automatically prune old backups.

## Notifications

| Type | Description | Docs |
|------|-------------|------|
| `smtp` | Email via SMTP | [docs/notifications/smtp.md](docs/notifications/smtp.md) |
| `slack` | Slack Incoming Webhook | [docs/notifications/slack.md](docs/notifications/slack.md) |
| `discord` | Discord webhook | [docs/notifications/discord.md](docs/notifications/discord.md) |
| `telegram` | Telegram Bot API | [docs/notifications/telegram.md](docs/notifications/telegram.md) |
| `matrix` | Matrix room message | [docs/notifications/matrix.md](docs/notifications/matrix.md) |
| `flagfile` | Write a flag file for monitoring | [docs/notifications/flagfile.md](docs/notifications/flagfile.md) |
| `prometheus` | Push metrics to Prometheus Pushgateway | [docs/notifications/prometheus.md](docs/notifications/prometheus.md) |
| `elasticsearch` | Write stats documents to Elasticsearch | [docs/notifications/elasticsearch.md](docs/notifications/elasticsearch.md) |

## Scheduling

See [docs/scheduling.md](docs/scheduling.md) for setup with:
- **systemd timer** (recommended) — structured logging, dependency management, easy monitoring
- **cron** — simple alternative

## Development

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Docker

```bash
docker pull ghcr.io/rossigee/backups:latest
docker run --rm -v /etc/backups:/etc/backups ghcr.io/rossigee/backups:latest /etc/backups/production.json
```
