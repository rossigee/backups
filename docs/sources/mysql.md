# Source: MySQL

Backs up a MySQL/MariaDB database using `mysqldump`.

**Module**: `backups.sources.mysql`

## Example

```json
{
  "id": "livedb",
  "type": "mysql",
  "name": "Live Company Database",
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
| `dbhost` | Yes | MySQL hostname. |
| `dbname` | Yes | Database name(s) to dump (space-separated for multiple). |
| `dbuser` | Yes | MySQL username. |
| `dbpass` | Yes | MySQL password. |
| `defaults` | No | Path to an existing `.my.cnf` file to use instead of generating one. |
| `options` | No | Extra options string passed to `mysqldump` (e.g. `"--single-transaction --skip-triggers"`). |
| `noevents` | No | Set to `1` to omit the `--events` flag from `mysqldump`. |
| `passphrase` | No | Passphrase for symmetric GPG encryption. |
| `recipients` | No | Array of GPG key recipients for asymmetric encryption. |
| `compress_only` | No | Set to `1` to skip encryption and only compress. |

## Notes

A temporary `.my.cnf` credentials file is created (mode `0400`) for the duration of the dump and removed afterwards.

If `--all-databases` is included in `options`, the `dbname` parameter is ignored.
