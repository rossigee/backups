# Destination: Minio / S3-Compatible

Uploads backups to a Minio bucket or any S3-compatible service (DigitalOcean Spaces, Wasabi, etc.) using the native `minio` Python SDK.

**Module**: `backups.destinations.minio`

## Example

```json
{
  "id": "minio-backup",
  "type": "minio",
  "endpoint": "nyc3.digitaloceanspaces.com",
  "bucket": "my-backup-bucket",
  "secure": true,
  "credentials": {
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY"
  },
  "retention_copies": 5,
  "retention_days": 30
}
```

For a local Minio instance:

```json
{
  "endpoint": "localhost:9000",
  "secure": false
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this destination. |
| `endpoint` | Yes | Service endpoint — host or `host:port`, no scheme (e.g. `nyc3.digitaloceanspaces.com`). |
| `bucket` | Yes | Bucket name. |
| `secure` | No | Use TLS (default: `true`). Set to `false` for local dev. |
| `credentials.access_key` | Yes | Access key. |
| `credentials.secret_key` | Yes | Secret key. |
| `retention_copies` | No | Number of most recent backups to keep. |
| `retention_days` | No | Delete backups older than this many days. |

## Backup path format

```
{endpoint}/{bucket}/{source_id}/{timestamp}/{filename}
```
