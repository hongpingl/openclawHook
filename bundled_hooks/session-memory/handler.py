"""
Session Memory Hook Handler

Saves session context to memory when you issue /new.
"""

import os
from datetime import datetime

from hook.hook_types import HookEvent, get_default_workspace_dir


def handler(event: HookEvent) -> None:
    """
    Handle command:new events to save session memory.
    
    Args:
        event: The hook event
    """
    if event.type != "command" or event.action != "new":
        return

    context = event.context
    if isinstance(context, dict):
        workspace_dir = context.get("workspace_dir") or get_default_workspace_dir()
    else:
        workspace_dir = get_default_workspace_dir()

    memory_dir = os.path.join(workspace_dir, "memory")
    os.makedirs(memory_dir, exist_ok=True)

    timestamp = event.timestamp.strftime("%Y-%m-%d-%H%M")
    filename = f"{timestamp}.md"
    filepath = os.path.join(memory_dir, filename)

    content = f"""# Session: {event.timestamp.isoformat()}

- **Session Key**: {event.session_key}
- **Timestamp**: {event.timestamp.isoformat()}
- **Action**: {event.action}

## Context

```json
{event.to_dict()}
```
"""

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[session-memory] Saved session to {filepath}")
        event.messages.append(f"💾 Session saved to {filename}")
    except Exception as e:
        print(f"[session-memory] Error saving session: {e}")


export = handler
