# Notification: Matrix

Posts backup notifications to a Matrix room via the Matrix Client-Server API.

**Module**: `backups.notifications.matrix`

## Example

```json
{
  "id": "matrix-notify",
  "type": "matrix",
  "url": "https://matrix.example.com",
  "room_id": "!yourRoomId:example.com",
  "access_token": "YOUR_ACCESS_TOKEN"
}
```

## Setup

1. Create or use an existing Matrix user for the bot.
2. Generate an access token (log in via the Element client and copy from Settings → Help & About → Access Token, or use the Matrix API directly).
3. Invite the bot user to the room and note the room's full ID (e.g. `!abc123:example.com`).

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this notification. |
| `url` | Yes | Base URL of the Matrix homeserver (e.g. `https://matrix.example.com`). |
| `room_id` | Yes | Full Matrix room ID (e.g. `!roomid:server.com`). |
| `access_token` | Yes | Matrix access token for the bot user. |

## Events

- **Success**: Posts a text message with the backup source name and size.
- **Failure**: Posts the error message.
