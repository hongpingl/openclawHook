"""
Message Logger Hook Handler

Logs all message events (received and sent).
"""

import os

from hook.hook_types import HookEvent


def handler(event: HookEvent) -> None:
    """
    Handle message events to log them.
    
    Args:
        event: The hook event
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
        preview = content[:50] + "..." if len(content) > 50 else content
        print(f"[message-logger] Received from {from_id} via {channel}: {preview}")
        
    elif event.action == "sent":
        to = context.get("to", "unknown")
        content = context.get("content", "")
        success = context.get("success", False)
        preview = content[:50] + "..." if len(content) > 50 else content
        status = "sent" if success else "failed"
        print(f"[message-logger] {status} to {to}: {preview}")


export = handler
