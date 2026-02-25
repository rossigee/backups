# Source: RDS PostgreSQL

Backs up an Amazon RDS PostgreSQL instance by restoring its most recent automated snapshot to a temporary RDS instance, running `pg_dump` against it, then deleting the temporary instance.

**Module**: `backups.sources.rdspostgresql`

> **Warning**: This can take a very long time depending on database size and RDS restore speed.

## Example

```json
{
  "id": "livedb-rds-pg",
  "type": "rds-pgsql",
  "name": "Live RDS PostgreSQL Database",
  "instancename": "my-rds-pg-instance",
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
| `dbname` | Yes | PostgreSQL database name to dump. |
| `dbuser` | Yes | PostgreSQL username. |
| `dbpass` | Yes | PostgreSQL password. |
| `credentials` | No | Object with `aws_access_key_id` and `aws_secret_access_key`. Falls back to standard AWS credential chain if omitted. |
| `passphrase` | No | Passphrase for symmetric GPG encryption. |
| `recipients` | No | Array of GPG key recipients for asymmetric encryption. |
