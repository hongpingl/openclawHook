---
name: conversation-saver
description: "Saves conversation (user input and assistant output) to JSONL file"
metadata:
  openclaw:
    emoji: "💬"
    events: ["message:received", "message:sent"]
---

# Conversation Saver Hook

Saves conversation messages to a JSONL file for later analysis or replay.

## What It Does

- Listens for `message:received` (user input) and `message:sent` (assistant output) events
- Saves each message as a JSON line with role, content, and timestamp
- Creates session-based files named `session_[timestamp].jsonl`

## Output

Files are saved to `<workspace>/conversations/session_YYYYMMDD_HHMMSS.jsonl`

## Example Output

```jsonl
{"role": "user", "content": "Hello, nanobot!", "timestamp": "2026-02-28T16:20:00.000000"}
{"role": "assistant", "content": "Hello! How can I help you today?", "timestamp": "2026-02-28T16:20:01.000000"}
```

## Requirements

None.

## Configuration

No additional configuration needed. Enable with:

```bash
openclaw hooks enable conversation-saver
```
