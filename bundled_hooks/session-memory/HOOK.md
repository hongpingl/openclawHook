---
name: session-memory
description: "Saves session context to memory when you issue /new"
homepage: https://docs.openclaw.ai/automation/hooks#session-memory
metadata:
  openclaw:
    emoji: "💾"
    events: ["command:new"]
    requires:
      config: ["workspace.dir"]
---

# Session Memory Hook

Saves session context to your agent workspace when you issue `/new`.

## What It Does

- Uses the pre-reset session entry to locate the correct transcript
- Extracts conversation history
- Saves session metadata to a dated memory file

## Output

Files are saved to `<workspace>/memory/YYYY-MM-DD-slug.md` (defaults to `~/.openclaw/workspace/memory/`)

## Example Output

```markdown
# Session: 2024-01-16 14:30:00 UTC

- **Session Key**: agent:main:main
- **Session ID**: abc123def456
- **Source**: telegram
```

## Requirements

- `workspace.dir` must be configured in your OpenClaw config

## Configuration

No additional configuration needed. Enable with:

```bash
openclaw hooks enable session-memory
```
