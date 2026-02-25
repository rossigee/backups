# Source: Folder

Backs up a local directory using `tar`.

**Module**: `backups.sources.folder`

## Example

```json
{
  "id": "config",
  "type": "folder",
  "name": "Live server config",
  "path": "/etc",
  "excludes": ["tmp", "*~"],
  "passphrase": "your-encryption-passphrase"
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this source. |
| `name` | No | Description for reporting (defaults to `id`). |
| `path` | Yes | Directory to back up. |
| `excludes` | No | Array of `--exclude` patterns passed to `tar`. |
| `passphrase` | No | Passphrase for symmetric GPG encryption. |
| `recipients` | No | Array of GPG key recipients for asymmetric encryption. |
| `compress_only` | No | Set to `1` to skip encryption and only compress. |

## Notes

If the path requires root access, the script calls `sudo tar`. Ensure the `backups` user has the appropriate sudoers entry:

```
backups ALL=(ALL) NOPASSWD: /bin/tar
```
