# Source: Volume Snapshot

Issues EC2/EBS volume snapshot commands via the AWS API.

**Module**: `backups.sources.snapshot`

> **Note**: This plugin is largely unmaintained. It leaves a small status file as its "dump", giving destination plugins something to process — it does not produce a restorable backup file.

## Example

```json
{
  "id": "livedb-volume",
  "type": "snapshot",
  "name": "Live DB EBS Volume",
  "instancename": "maindb1",
  "credentials": {
    "aws_access_key_id": "YOUR_ACCESS_KEY_ID",
    "aws_secret_access_key": "YOUR_SECRET_ACCESS_KEY"
  }
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this source. |
| `name` | No | Description for reporting (defaults to `id`). |
| `volume_id` | No | EBS volume ID to snapshot. |
| `availability_zone` | No | AWS availability zone. |
| `credentials` | No | Object with `aws_access_key_id` and `aws_secret_access_key`. |
