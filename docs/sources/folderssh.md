# Source: Folder via SSH

Backs up a remote directory over SSH using `tar`.

**Module**: `backups.sources.folderssh`

## Example

```json
{
  "id": "remote-config",
  "type": "folder-ssh",
  "name": "Remote server config",
  "sshhost": "server.example.com",
  "sshuser": "backups",
  "path": "/etc",
  "excludes": ["tmp"],
  "passphrase": "your-encryption-passphrase"
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this source. |
| `name` | No | Description for reporting (defaults to `id`). |
| `sshhost` | Yes | Remote hostname to connect to. |
| `sshuser` | Yes | SSH username. |
| `path` | Yes | Remote directory to back up. |
| `excludes` | No | Array of `--exclude` patterns passed to `tar`. |
| `passphrase` | No | Passphrase for symmetric GPG encryption. |
| `recipients` | No | Array of GPG key recipients for asymmetric encryption. |
| `compress_only` | No | Set to `1` to skip encryption and only compress. |

## Notes

The backup host must have passwordless SSH access to the remote host for the configured user. Add the backup host's public key to `~/.ssh/authorized_keys` on the remote.
