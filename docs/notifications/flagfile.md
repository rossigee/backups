# Notification: Flag File

Writes a flag file on successful backup completion. Useful for monitoring via tools like Nagios, Icinga, or custom watchdog scripts that check file modification times.

**Module**: `backups.notifications.flagfile`

## Example

```json
{
  "id": "flagfile-notify",
  "type": "flagfile",
  "flagfile": "/var/run/backup-ok"
}
```

## Setup

Ensure the backup process has write permission to the target path and that the monitoring system checks the file's modification time.

Example Nagios/Icinga check using `check_file_age`:

```bash
check_file_age -f /var/run/backup-ok -w 86400 -c 172800
```

This warns if the file is older than 24 hours and alerts if older than 48 hours.

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `flagfile` | Yes | Absolute path to the flag file to write on success. |

## Events

- **Success**: Writes `OK` to the flag file, updating its modification time.
- **Failure**: Does nothing (flag file is not updated, so it grows stale).
