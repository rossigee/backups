# Notification: Slack

Posts backup notifications to a Slack channel via an Incoming Webhook.

**Module**: `backups.notifications.slack`

## Example

```json
{
  "id": "slack-notify",
  "type": "slack",
  "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
}
```

## Setup

1. Go to your Slack workspace's **Apps** settings and add the **Incoming WebHooks** app.
2. Choose a channel and create a webhook.
3. Copy the webhook URL into the `url` field.

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `url` | Yes | Slack Incoming Webhook URL. |

## Events

- **Start**: Posts a message when the backup begins.
- **Success**: Posts backup size and timing breakdown (dump time, encrypt time, upload time).
- **Failure**: Posts the error message.
