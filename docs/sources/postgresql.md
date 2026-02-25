# Source: PostgreSQL

Backs up a PostgreSQL database using `pg_dump`.

**Module**: `backups.sources.postgresql`

## Example

```json
{
  "id": "livedb",
  "type": "pgsql",
  "name": "Live PostgreSQL Database",
  "dbhost": "localhost",
  "dbname": "livecompany",
  "dbuser": "backups",
  "dbpass": "readonly-password",
  "passphrase": "your-encryption-passphrase"
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this source. |
| `name` | No | Description for reporting (defaults to `id`). |
| `dbhost` | Yes | PostgreSQL hostname. |
| `dbname` | Yes | Database name to dump. |
| `dbuser` | Yes | PostgreSQL username. |
| `dbpass` | Yes | PostgreSQL password. |
| `defaults` | No | Path to an existing `.pgpass` file to use instead of generating one. |
| `passphrase` | No | Passphrase for symmetric GPG encryption. |
| `recipients` | No | Array of GPG key recipients for asymmetric encryption. |
| `compress_only` | No | Set to `1` to skip encryption and only compress. |

## Notes

A temporary `.pgpass` file is created (mode `0400`) for the duration of the dump and removed afterwards.
