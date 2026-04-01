"""
Hello World Hook

A simple example hook that prints hello messages.
"""

from hook.hook_types import HookEvent


def handler(event: HookEvent) -> None:
    """
    Handle events and print hello messages.
    
    Args:
        event: The hook event
    """
    print(f"[hello-world]表示是hello-world钩子内部功能")
    print(f"[hello-world] Hello! Event received:")
    print(f"[hello-world]  - Type: {event.type}")
    print(f"[hello-world]  - Action: {event.action}")
    print(f"[hello-world]  - Session Key: {event.session_key}")
    print(f"[hello-world]  - Timestamp: {event.timestamp}")
    if event.messages:
        print(f"[hello-world]  - Messages: {event.messages}")
    print(f"[hello-world] World says: Hook executed successfully!")


export = handler
