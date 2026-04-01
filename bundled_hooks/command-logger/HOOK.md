---
name: command-logger
description: "Logs all command events to a centralized audit file"
homepage: https://docs.openclaw.ai/automation/hooks#command-logger
metadata:
  openclaw:
    emoji: "📝"
    events: ["command"]
---

# Command Logger Hook

Logs all command events to a centralized audit file for troubleshooting or compliance.

## What It Does

- Captures event details (command action, timestamp, session key, sender ID, source)
- Appends to log file in JSONL format
- Runs silently in the background

## Output

Logs are written to `~/.openclaw/logs/commands.log`

## Example Log Entries

```json
{"timestamp":"2024-01-16T14:30:00.000Z","action":"new","sessionKey":"agent:main:main","senderId":"+1234567890","source":"telegram"}
{"timestamp":"2024-01-16T15:45:22.000Z","action":"stop","sessionKey":"agent:main:main","senderId":"user@example.com","source":"whatsapp"}
```

## Usage

View logs:

```bash
# View recent commands
tail -n 20 ~/.openclaw/logs/commands.log

# Pretty-print with jq
cat ~/.openclaw/logs/commands.log | jq .

# Filter by action
grep '"action":"new"' ~/.openclaw/logs/commands.log | jq .
```

## Requirements

None.

## Configuration

No configuration needed. Enable with:

```bash
openclaw hooks enable command-logger
```
