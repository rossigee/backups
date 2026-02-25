# Destination: Google Drive

Uploads backups to a Google Drive folder using `google-api-python-client` with service account authentication.

**Module**: `backups.destinations.gdrive`

## Example

```json
{
  "id": "gdrive-backup",
  "type": "gdrive",
  "creds_file": "/etc/backups/gdrive-service-account.json",
  "folder_id": "YOUR_GOOGLE_DRIVE_FOLDER_ID",
  "retention_copies": 10,
  "retention_days": 90
}
```

## Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com) and create (or select) a project.
2. Enable the **Google Drive API** for the project.
3. Create a **service account** and download the JSON key file.
4. Place the key file on the backup host (e.g. `/etc/backups/gdrive-service-account.json`, mode `0400`).
5. In Google Drive, create a folder for backups, then **share it** with the service account email address (grant **Editor** permission).
6. Copy the folder ID from the Drive URL (the long string after `/folders/`).

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this destination. |
| `creds_file` | Yes | Path to the service account JSON key file. |
| `folder_id` | Yes | Google Drive folder ID to store backups in. |
| `retention_copies` | No | Number of most recent timestamped sub-folders to keep. |
| `retention_days` | No | Delete backup folders older than this many days. |

## Backup structure

```
{folder_id}/
  {source_id}/
    {timestamp}/
      {filename}
```
