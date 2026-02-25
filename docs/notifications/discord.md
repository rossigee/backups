# Notification: Discord

Posts backup notifications to a Discord channel via a webhook.

**Module**: `backups.notifications.discord`

## Example

```json
{
  "id": "discord-notify",
  "type": "discord",
  "url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
}
```

## Setup

1. In your Discord server, go to **Server Settings → Integrations → Webhooks**.
2. Create a new webhook for the channel where you want notifications.
3. Copy the webhook URL into the `url` field.

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `url` | Yes | Discord webhook URL. |

## Events

- **Success**: Posts a message with the backup source name and size.
- **Failure**: Posts the error message.
