---
name: message-logger
description: "Logs all message events (received and sent)"
metadata:
  openclaw:
    emoji: "📨"
    events: ["message:received", "message:sent"]
---

# Message Logger Hook

Logs all message events for debugging and auditing purposes.

## What It Does

- Logs received messages with sender info
- Logs sent messages with recipient info and status
- Includes channel and content preview

## Events

- `message:received` - When an inbound message is received
- `message:sent` - When an outbound message is sent

## Example Output

```
[message-logger] Received from +1234567890 via whatsapp: Hello, how can I...
[message-logger] sent to +1234567890: Thanks for your message!...
```

## Requirements

None.

## Configuration

No configuration needed. Enable with:

```bash
openclaw hooks enable message-logger
```
