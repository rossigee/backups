# Destination: Dropbox

Uploads backups to a Dropbox folder using the official `dropbox` Python SDK.

**Module**: `backups.destinations.dropbox`

## Example

```json
{
  "id": "dropbox-backup",
  "type": "dropbox",
  "access_token": "YOUR_LONG_LIVED_ACCESS_TOKEN",
  "folder": "/backups",
  "retention_copies": 7
}
```

## Setup

1. Go to https://www.dropbox.com/developers/apps and create a new app.
2. Choose **Scoped access** → **Full Dropbox** (or a specific folder).
3. Under **Permissions**, enable `files.content.write` and `files.content.read`.
4. Generate a long-lived access token from the **Settings** tab.

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this destination. |
| `access_token` | Yes | Dropbox long-lived access token. |
| `folder` | No | Root folder path within Dropbox (default: `/backups`). |
| `retention_copies` | No | Number of most recent timestamped directories to keep. |

## Backup path format

```
{folder}/{source_id}/{timestamp}/{filename}
```
