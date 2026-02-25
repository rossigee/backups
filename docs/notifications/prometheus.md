# Notification: Prometheus Pushgateway

Pushes backup metrics to a Prometheus Pushgateway after each successful backup.

**Module**: `backups.notifications.prometheus`

## Example

```json
{
  "id": "prometheus-notify",
  "type": "prometheus",
  "url": "http://pushgateway.monitoring.svc:9091",
  "credentials": {
    "username": "pushgw",
    "password": "YOUR_PASSWORD"
  }
}
```

Without authentication:

```json
{
  "id": "prometheus-notify",
  "type": "prometheus",
  "url": "http://pushgateway.monitoring.svc:9091"
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `url` | Yes | URL of the Prometheus Pushgateway. |
| `credentials.username` | No | Basic auth username for the Pushgateway. |
| `credentials.password` | No | Basic auth password for the Pushgateway. |

## Metrics pushed

| Metric | Type | Description |
|--------|------|-------------|
| `backup_size` | Summary | Size of the backup file in bytes. |
| `backup_dumptime` | Summary | Time taken to dump and compress/encrypt the backup (seconds). |
| `backup_uploadtime` | Summary | Time taken to upload the backup (seconds). |
| `backup_retained_copies` | Gauge | Number of retained backup copies on the destination. |
| `backup_timestamp` | Gauge | Unix timestamp when the backup completed. |

Metrics are pushed with `job=<source_id>`, allowing per-source alerting rules.

## Events

- **Success**: Pushes all metrics to the gateway.
- **Failure**: Not reported (consider pairing with a [flag file](flagfile.md) for failure detection).
