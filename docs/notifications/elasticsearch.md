# Notification: Elasticsearch

Writes backup statistics as JSON documents to an Elasticsearch index, enabling historical analysis and dashboards (e.g. Kibana).

**Module**: `backups.notifications.elasticsearch`

## Example

```json
{
  "id": "elasticsearch-notify",
  "type": "elasticsearch",
  "url": "https://elasticsearch.logging.svc:9200",
  "indexpattern": "backups-%Y.%m",
  "credentials": {
    "username": "elastic",
    "password": "YOUR_PASSWORD"
  }
}
```

Without authentication:

```json
{
  "id": "elasticsearch-notify",
  "type": "elasticsearch",
  "url": "http://localhost:9200",
  "indexpattern": "backups-%Y.%m.%d"
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `url` | Yes | Elasticsearch endpoint URL. |
| `indexpattern` | Yes | `strftime`-compatible index name pattern (e.g. `backups-%Y.%m` for monthly indices). |
| `credentials.username` | No | Basic auth username. |
| `credentials.password` | No | Basic auth password. |

## Document structure

### Success

```json
{
  "@timestamp": "2025-01-15T03:00:01.123456",
  "status": "success",
  "source": { "id": "my-db", "name": "My Database" },
  "hostname": "backup-host",
  "stats": {
    "starttime": "2025-01-15T03:00:00.000000",
    "endtime": "2025-01-15T03:00:01.000000",
    "size": 1048576,
    "dumptime": 0.8,
    "dumpedfiles": 1,
    "uploadtime": 0.2,
    "retainedfiles": 5
  }
}
```

### Failure

```json
{
  "status": "failed",
  "source": { "id": "my-db", "name": "My Database" },
  "hostname": "backup-host",
  "error": "Connection refused"
}
```

## Events

- **Success**: Writes a document with full statistics.
- **Failure**: Writes a document with the error message.
