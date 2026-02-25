# Destination: Local Filesystem

Copies backups to a local filesystem path. Useful for NFS mounts, USB drives, or any locally accessible storage.

**Module**: `backups.destinations.local`

## Example

```json
{
  "id": "local-backup",
  "type": "local",
  "path": "/mnt/backup-drive",
  "retention_copies": 7,
  "retention_days": 30
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this destination. |
| `path` | Yes | Filesystem path to copy backups into. |
| `retention_copies` | No | Number of most recent timestamped directories to keep. |
| `retention_days` | No | Delete backup directories older than this many days. |

## Backup path format

```
{path}/{source_id}/{timestamp}/{filename}
```

Intermediate directories are created automatically.
