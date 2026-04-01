"""
Command Logger Hook Handler

Logs all command events to a centralized audit file.
"""

import json
import os
import sys

# Add the hook directory to Python path
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hook.hook_types import HookEvent, get_default_logs_dir


def handler(event: HookEvent) -> None:
    """
    Handle command events to log them.
    
    Args:
        event: The hook event
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
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[command-logger] Error logging command: {e}")


export = handler
