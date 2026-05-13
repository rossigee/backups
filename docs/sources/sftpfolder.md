# Source: Folder via SFTP

Backs up a remote directory over SFTP by recursively walking and packing files into a tar archive.

**Module**: `backups.sources.sftpfolder`

## Example

```json
{
  "id": "remote-data",
  "type": "sftp-folder",
  "name": "Remote server data",
  "sshhost": "server.example.com",
  "sshuser": "backups",
  "path": "/var/www",
  "password": "your-sftp-password",
  "excludes": ["*.log", "cache/"],
  "passphrase": "your-encryption-passphrase"
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this source. |
| `name` | No | Description for reporting (defaults to `id`). |
| `sshhost` | Yes | Remote hostname to connect to. |
| `sshuser` | Yes | SFTP username. |
| `path` | Yes | Remote directory to back up. |
| `sshport` | No | SSH port (defaults to `22`). |
| `password` | No | Password for password-based authentication. |
| `key_filename` | No | Path to a private key file for key-based authentication. |
| `excludes` | No | Array of glob patterns (fnmatch) to exclude from the backup. Patterns are matched against both the filename and the archive path. |
| `passphrase` | No | Passphrase for symmetric GPG encryption. |
| `recipients` | No | Array of GPG key recipients for asymmetric encryption. |
| `compress_only` | No | Set to `1` to skip encryption and only compress. |

## Notes

The backup host must have network access to the remote host on the configured port. Authentication can use either a password or an SSH private key.
