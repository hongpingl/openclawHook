"""
Conversation Saver Hook Handler

Saves conversation (user input and assistant output) to JSONL file.
"""

import os
import json
from datetime import datetime

from hook.hook_types import HookEvent, get_default_workspace_dir


_session_files = {}

def _get_session_file(workspace_dir: str, session_key: str) -> str:
    """
    Get or create the session file path for a given session.
    
    Args:
        workspace_dir: The workspace directory
        session_key: The session identifier
        
    Returns:
        The path to the session JSONL file
    """
    if session_key not in _session_files:
        conversations_dir = os.path.join(workspace_dir, "conversations")
        os.makedirs(conversations_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.jsonl"
        _session_files[session_key] = os.path.join(conversations_dir, filename)
    
    return _session_files[session_key]


def _save_message(filepath: str, role: str, content: str, timestamp: str) -> None:
    """
    Save a message to the JSONL file.
    
    Args:
        filepath: The path to the JSONL file
        role: The role (user or assistant)
        content: The message content
        timestamp: The timestamp string
    """
    record = {
        "role": role,
        "content": content,
        "timestamp": timestamp
    }
    
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[conversation-saver] Error saving message: {e}")


def handler(event: HookEvent) -> None:
    """
    Handle message events to save conversation.
    
    Args:
        event: The hook event
    """
    if event.type != "message":
        return
    
    context = event.context
    if not isinstance(context, dict):
        return
    
    workspace_dir = context.get("workspace_dir") or get_default_workspace_dir()
    session_key = event.session_key or "default_session"
    filepath = _get_session_file(workspace_dir, session_key)
    
    timestamp = datetime.now().isoformat()
    
    if event.action == "received":
        content = context.get("content", "")
        if content:
            _save_message(filepath, "user", content, timestamp)
            print(f"[conversation-saver] Saved user message to {os.path.basename(filepath)}")
    
    elif event.action == "sent":
        content = context.get("content", "")
        if content:
            _save_message(filepath, "assistant", content, timestamp)
            print(f"[conversation-saver] Saved assistant message to {os.path.basename(filepath)}")


export = handler
