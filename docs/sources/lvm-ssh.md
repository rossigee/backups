# Source: LVM over SSH

Creates an LVM snapshot on a remote host via SSH.

**Module**: `backups.sources.lvmssh`

## Example

```json
{
  "id": "mydisk1",
  "type": "lvm-ssh",
  "name": "My LVM Volume",
  "sshhost": "hostname.domain.com",
  "sshuser": "root",
  "vg_name": "ubuntu-vg",
  "lv_name": "mydisk1",
  "size": "5G",
  "retain_snapshots": 3
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this source. |
| `name` | No | Description for reporting (defaults to `id`). |
| `sshhost` | Yes | Remote hostname to SSH to. |
| `sshuser` | Yes | SSH username (typically `root` for LVM access). |
| `vg_name` | Yes | LVM volume group name. |
| `lv_name` | Yes | LVM logical volume name. |
| `size` | Yes | Size of the snapshot volume (e.g. `5G`). |
| `retain_snapshots` | No | Number of snapshot volumes to retain on the remote host. |

## Notes

The backup host must have passwordless SSH access to the remote host. The SSH user needs sufficient privileges to run LVM commands.
