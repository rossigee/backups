# Source: RDS MySQL

Backs up an Amazon RDS MySQL instance by restoring its most recent automated snapshot to a temporary RDS instance, running `mysqldump` against it, then deleting the temporary instance. This avoids placing any load on the live database.

**Module**: `backups.sources.rds`

> **Warning**: This can take a very long time depending on database size and RDS restore speed.

## Example

```json
{
  "id": "livedb-rds",
  "type": "rds",
  "name": "Live RDS MySQL Database",
  "instancename": "my-rds-instance",
  "region": "eu-west-1",
  "security_group": "sg-xxxxxxxx",
  "instance_class": "db.t3.small",
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
| `instancename` | Yes | RDS instance identifier to restore a snapshot of. |
| `region` | Yes | AWS region of the RDS instance. |
| `security_group` | Yes | VPC security group ID to assign to the temporary instance (must allow inbound from this host). |
| `instance_class` | No | RDS instance class for the temporary instance (default: `db.t3.small`). |
| `dbname` | Yes | MySQL database name to dump. |
| `dbuser` | Yes | MySQL username. |
| `dbpass` | Yes | MySQL password. |
| `noevents` | No | Set to `1` to omit the `--events` flag from `mysqldump`. |
| `credentials` | No | Object with `aws_access_key_id` and `aws_secret_access_key`. Falls back to standard AWS credential chain if omitted. |
| `passphrase` | No | Passphrase for symmetric GPG encryption. |
| `recipients` | No | Array of GPG key recipients for asymmetric encryption. |

## AWS Credentials

If `credentials` are omitted, the standard AWS credential chain is used (`~/.aws/credentials`, IAM instance role, environment variables, etc.).
