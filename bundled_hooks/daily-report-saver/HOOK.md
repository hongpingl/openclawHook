---
name: daily-report-saver
description: "Saves daily report content to markdown file"
metadata:
  openclaw:
    emoji: "📝"
    events: ["message:sent"]
---

# Daily Report Saver Hook

Saves daily report content to a markdown file when a message is sent.

## What It Does

- Listens for `message:sent` events
- Saves the message content to a dated markdown file
- Organizes reports by date in the workspace directory

## Output

Files are saved to `<workspace>/reports/YYYY-MM-DD.md`

## Example Output

```markdown
# Daily Report - 2024-01-16

Content: Today I learned about the openclaw project...
```

## Requirements

None.

## Configuration

No additional configuration needed. Enable with:

```bash
openclaw hooks enable daily-report-saver
```
