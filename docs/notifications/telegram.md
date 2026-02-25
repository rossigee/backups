# Notification: Telegram

Sends backup notifications to a Telegram chat via the Bot API.

**Module**: `backups.notifications.telegram`

## Example

```json
{
  "id": "telegram-notify",
  "type": "telegram",
  "api_token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID"
}
```

## Setup

1. Open Telegram and message **@BotFather** to create a new bot. Note the API token it gives you.
2. Add the bot to your target group or channel.
3. To find your `chat_id`, send a message to the bot then call:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   The `chat.id` field in the response is your `chat_id`.

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `api_token` | Yes | Telegram Bot API token from @BotFather. |
| `chat_id` | Yes | Telegram chat or group ID to send messages to. |

## Events

- **Success**: Posts a message with the backup source name and size.
- **Failure**: Posts the error message.
