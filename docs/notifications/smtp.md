# Notification: SMTP Email

Sends email notifications on backup success and/or failure via SMTP.

**Module**: `backups.notifications.smtp`

## Example

```json
{
  "id": "email-notify",
  "type": "smtp",
  "host": "smtp.example.com",
  "port": 587,
  "use_tls": true,
  "use_ssl": false,
  "credentials": {
    "username": "backups@example.com",
    "password": "YOUR_SMTP_PASSWORD"
  },
  "success_to": "ops@example.com",
  "failure_to": "ops@example.com",
  "debug": false
}
```

For SSL on port 465:

```json
{
  "port": 465,
  "use_tls": false,
  "use_ssl": true
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `host` | Yes | SMTP server hostname. |
| `port` | Yes | SMTP server port (e.g. `587` for STARTTLS, `465` for SSL). |
| `use_tls` | Yes | Whether to use STARTTLS after connecting. |
| `use_ssl` | Yes | Whether to connect with SSL (SMTP_SSL). |
| `credentials.username` | Yes | SMTP authentication username. |
| `credentials.password` | Yes | SMTP authentication password. |
| `success_to` | No | Email address to notify on success. Leave empty to suppress success emails. |
| `failure_to` | No | Email address to notify on failure. Leave empty to suppress failure emails. |
| `debug` | No | Enable SMTP debug output (default: `false`). |

## Events

- **Success**: Sends email with backup size summary.
- **Failure**: Sends email with error details and traceback.
