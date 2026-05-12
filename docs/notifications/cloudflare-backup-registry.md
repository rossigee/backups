# Notification: Cloudflare Backup Registry

Posts backup run reports to the Cloudflare Backup Registry API.

**Module**: `backups.notifications.cloudflare_backup_registry`

## Example

```json
{
  "id": "cloudflare-backup-registry-notify",
  "type": "cloudflare-backup-registry",
  "url": "https://backups.golder.tech/v1/backup-runs",
  "token": "your_api_token",
  "metadata": {"environment": "production"}
}
```

## Setup

1. Ensure access to the Golder backup registry at the specified URL.
2. Obtain an API token if authentication is required.

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `url` | Yes | Golder API endpoint URL. |
| `token` | No | API token for Bearer authentication. |
| `metadata` | No | Arbitrary key/value pairs to include in the payload. |

## Events

- **Success**: Submits a backup run report with status "success".
- **Failure**: Submits a backup run report with status "failure".