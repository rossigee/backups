# Destination: Samba

Uploads backups to a Samba/SMB share using `smbclient`.

**Module**: `backups.destinations.samba`

## Example

```json
{
  "id": "samba-backup",
  "type": "samba",
  "host": "server1.local.lan",
  "share": "Backups",
  "workgroup": "WORKGROUP",
  "credentials": {
    "username": "backups",
    "password": "your-password"
  },
  "suffix": "gpg"
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this destination. |
| `host` | Yes | Samba server hostname. |
| `share` | Yes | Share name. |
| `workgroup` | Yes | Samba domain/workgroup. |
| `credentials.username` | Yes | Samba username. |
| `credentials.password` | Yes | Samba password. |
| `suffix` | Yes | File suffix for uploaded files (e.g. `gpg`). |

## Notes

Retention policies are not yet implemented for the Samba destination.
