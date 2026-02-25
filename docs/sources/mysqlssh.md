# Source: MySQL via SSH

Backs up a remote MySQL/MariaDB database over SSH using `mysqldump`.

**Module**: `backups.sources.mysqlssh`

## Example

```json
{
  "id": "remote-livedb",
  "type": "mysql-ssh",
  "name": "Remote Live Database",
  "sshhost": "db.example.com",
  "sshuser": "backups",
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
| `sshhost` | Yes | Remote hostname to SSH to. |
| `sshuser` | Yes | SSH username. |
| `dbhost` | Yes | MySQL hostname (as seen from the remote host). |
| `dbname` | Yes | Database name(s) to dump. |
| `dbuser` | Yes | MySQL username. |
| `dbpass` | Yes | MySQL password. |
| `options` | No | Extra options string passed to `mysqldump`. |
| `noevents` | No | Set to `1` to omit the `--events` flag. |
| `passphrase` | No | Passphrase for symmetric GPG encryption. |
| `recipients` | No | Array of GPG key recipients for asymmetric encryption. |
| `compress_only` | No | Set to `1` to skip encryption and only compress. |
