# Destination: Google Cloud Storage

Uploads backups to a Google Cloud Storage bucket. Uploads use `gsutil`; retention management uses the `google-cloud-storage` Python SDK.

**Module**: `backups.destinations.gs`

## Example

```json
{
  "id": "gcs-backup",
  "type": "gs",
  "bucket": "my-backup-bucket",
  "gcs_creds_path": "/etc/backups/gcs-service-account.json",
  "retention_copies": 7,
  "retention_days": 30
}
```

## Setup

1. Create a GCP service account with **Storage Object Admin** permission on the target bucket.
2. Download the JSON key file and place it on the backup host (e.g. `/etc/backups/gcs-service-account.json`, mode `0400`).
3. Authenticate `gsutil` with the same service account:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/etc/backups/gcs-service-account.json
   # or
   gcloud auth activate-service-account --key-file=/etc/backups/gcs-service-account.json
   ```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this destination. |
| `bucket` | Yes | GCS bucket name. |
| `gcs_creds_path` | Yes | Path to the service account JSON key file. |
| `retention_copies` | No | Number of most recent backups to keep. |
| `retention_days` | No | Delete backups older than this many days. |
