"""
Bundled hooks for the OpenClaw Hooks System.
"""

import os
from datetime import datetime
from typing import Any, Dict, List

from hook_types import HookEvent
from hook_types import get_default_logs_dir, get_default_workspace_dir


def session_memory_handler(event: HookEvent) -> None:
    """
    Saves session context to memory when you issue /new.
    
    Events: command:new
    Requirements: workspace.dir must be configured
    Output: <workspace>/memory/YYYY-MM-DD-slug.md
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
    except Exception as e:
        print(f"[session-memory] Error saving session: {e}")


def command_logger_handler(event: HookEvent) -> None:
    """
    Logs all command events to a centralized audit file.
    
    Events: command
    Requirements: None
    Output: ~/.openclaw/logs/commands.log
    """
    if event.type != "command":
        return

    logs_dir = get_default_logs_dir()
    os.makedirs(logs_dir, exist_ok=True)

    log_file = os.path.join(logs_dir, "commands.log")

    log_entry = {
        "timestamp": event.timestamp.isoformat(),
        "action": event.action,
        "sessionKey": event.session_key,
    }

    context = event.context
    if isinstance(context, dict):
        if "sender_id" in context:
            log_entry["senderId"] = context["sender_id"]
        if "command_source" in context:
            log_entry["source"] = context["command_source"]

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{log_entry}\n")
    except Exception as e:
        print(f"[command-logger] Error logging command: {e}")


def bootstrap_extra_files_handler(event: HookEvent) -> None:
    """
    Injects additional bootstrap files during agent:bootstrap.
    
    Events: agent:bootstrap
    Requirements: workspace.dir must be configured
    """
    if event.type != "agent" or event.action != "bootstrap":
        return

    context = event.context
    if not isinstance(context, dict):
        return

    bootstrap_files = context.get("bootstrap_files", [])
    workspace_dir = context.get("workspace_dir")

    if not workspace_dir:
        return

    extra_patterns = context.get("extra_patterns", [])
    for pattern in extra_patterns:
        import glob
        for filepath in glob.glob(pattern, recursive=True):
            real_path = os.path.realpath(filepath)
            real_workspace = os.path.realpath(workspace_dir)

            if not real_path.startswith(real_workspace):
                continue

            if os.path.isfile(real_path):
                bootstrap_files.append({
                    "path": real_path,
                    "basename": os.path.basename(real_path),
                })

    print(f"[bootstrap-extra-files] Added {len(extra_patterns)} extra bootstrap patterns")


def boot_md_handler(event: HookEvent) -> None:
    """
    Runs BOOT.md when the gateway starts.
    
    Events: gateway:startup
    Requirements: workspace.dir must be configured
    """
    if event.type != "gateway" or event.action != "startup":
        return

    context = event.context
    if isinstance(context, dict):
        workspace_dir = context.get("workspace_dir") or get_default_workspace_dir()
    else:
        workspace_dir = get_default_workspace_dir()

    boot_md_path = os.path.join(workspace_dir, "BOOT.md")

    if not os.path.isfile(boot_md_path):
        print("[boot-md] No BOOT.md found in workspace")
        return

    try:
        with open(boot_md_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"[boot-md] Loaded BOOT.md ({len(content)} bytes)")
    except Exception as e:
        print(f"[boot-md] Error reading BOOT.md: {e}")


def message_logger_handler(event: HookEvent) -> None:
    """
    Logs all message events.
    
    Events: message:received, message:sent
    """
    if event.type != "message":
        return

    context = event.context
    if not isinstance(context, dict):
        return

    if event.action == "received":
        from_id = context.get("from", "unknown")
        content = context.get("content", "")
        channel = context.get("channelId", "unknown")
        print(f"[message-logger] Received from {from_id} via {channel}: {content[:50]}...")
    elif event.action == "sent":
        to = context.get("to", "unknown")
        content = context.get("content", "")
        success = context.get("success", False)
        status = "sent" if success else "failed"
        print(f"[message-logger] {status} to {to}: {content[:50]}...")


BUNDLED_HOOKS = {
    "session-memory": {
        "handler": session_memory_handler,
        "description": "Saves session context to memory when you issue /new",
        "emoji": "💾",
        "events": ["command:new"],
    },
    "command-logger": {
        "handler": command_logger_handler,
        "description": "Logs all command events to a centralized audit file",
        "emoji": "📝",
        "events": ["command"],
    },
    "bootstrap-extra-files": {
        "handler": bootstrap_extra_files_handler,
        "description": "Injects additional bootstrap files during agent:bootstrap",
        "emoji": "📎",
        "events": ["agent:bootstrap"],
    },
    "boot-md": {
        "handler": boot_md_handler,
        "description": "Runs BOOT.md when the gateway starts",
        "emoji": "🚀",
        "events": ["gateway:startup"],
    },
    "message-logger": {
        "handler": message_logger_handler,
        "description": "Logs all message events",
        "emoji": "📨",
        "events": ["message:received", "message:sent"],
    },
}


def get_bundled_hook(name: str):
    """Get a bundled hook by name."""
    return BUNDLED_HOOKS.get(name)


def list_bundled_hooks() -> List[str]:
    """List all bundled hook names."""
    return list(BUNDLED_HOOKS.keys())
