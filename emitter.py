"""
Event emitter for the OpenClaw Hooks System.
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from .hook_types import (
    HookEvent,
    HookEventType,
    HookHandler,
)


class EventEmitter:
    """
    Event emitter that manages event listeners and emits events to hooks.
    
    Supports both synchronous and asynchronous handlers.
    """

    def __init__(self):
        self._listeners: Dict[str, List[HookHandler]] = {}
        self._wildcard_listeners: List[HookHandler] = []
        self._type_listeners: Dict[str, List[HookHandler]] = {}

    def on(self, event: str, handler: HookHandler) -> None:
        """
        Register a handler for a specific event.

        Args:
            event: Event name (e.g., "command:new", "message:received")
            handler: The handler function
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(handler)

    def on_type(self, event_type: str, handler: HookHandler) -> None:
        """
        Register a handler for all events of a specific type.

        Args:
            event_type: Event type (e.g., "command", "message")
            handler: The handler function
        """
        if event_type not in self._type_listeners:
            self._type_listeners[event_type] = []
        self._type_listeners[event_type].append(handler)

    def on_any(self, handler: HookHandler) -> None:
        """
        Register a handler for all events.

        Args:
            handler: The handler function
        """
        self._wildcard_listeners.append(handler)

    def off(self, event: str, handler: HookHandler) -> bool:
        """
        Unregister a handler from a specific event.

        Args:
            event: Event name
            handler: The handler to remove

        Returns:
            True if the handler was removed, False if not found
        """
        if event in self._listeners and handler in self._listeners[event]:
            self._listeners[event].remove(handler)
            return True
        return False

    def off_type(self, event_type: str, handler: HookHandler) -> bool:
        """
        Unregister a handler from an event type.

        Args:
            event_type: Event type
            handler: The handler to remove

        Returns:
            True if the handler was removed, False if not found
        """
        if event_type in self._type_listeners and handler in self._type_listeners[event_type]:
            self._type_listeners[event_type].remove(handler)
            return True
        return False

    def off_any(self, handler: HookHandler) -> bool:
        """
        Unregister a handler from all events.

        Args:
            handler: The handler to remove

        Returns:
            True if the handler was removed, False if not found
        """
        if handler in self._wildcard_listeners:
            self._wildcard_listeners.remove(handler)
            return True
        return False

    def emit(self, event: HookEvent) -> List[str]:
        """
        Emit an event to all registered handlers.

        Args:
            event: The event to emit

        Returns:
            List of messages from handlers
        """
        handlers = self._get_handlers_for_event(event)

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception as e:
                print(f"[EventEmitter] Handler error: {e}")

        return event.messages

    async def emit_async(self, event: HookEvent) -> List[str]:
        """
        Emit an event asynchronously to all registered handlers.

        Args:
            event: The event to emit

        Returns:
            List of messages from handlers
        """
        handlers = self._get_handlers_for_event(event)

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"[EventEmitter] Handler error: {e}")

        return event.messages

    def _get_handlers_for_event(self, event: HookEvent) -> List[HookHandler]:
        """
        Get all handlers that should be called for an event.

        Args:
            event: The event

        Returns:
            List of handlers to call
        """
        handlers: List[HookHandler] = []

        handlers.extend(self._wildcard_listeners)

        event_type = event.type.value if isinstance(event.type, HookEventType) else event.type
        if event_type in self._type_listeners:
            handlers.extend(self._type_listeners[event_type])

        event_key = f"{event_type}:{event.action}"
        if event_key in self._listeners:
            handlers.extend(self._listeners[event_key])

        return handlers

    def create_event(
        self,
        event_type: HookEventType,
        action: str,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> HookEvent:
        """
        Create a new hook event.

        Args:
            event_type: The type of event
            action: The action that triggered the event
            session_key: The session identifier
            context: Optional context data

        Returns:
            A new HookEvent instance
        """
        return HookEvent(
            type=event_type,
            action=action,
            session_key=session_key,
            timestamp=datetime.now(),
            messages=[],
            context=context or {},
        )

    def emit_command(
        self,
        action: str,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a command event.

        Args:
            action: The command action (e.g., "new", "reset", "stop")
            session_key: The session identifier
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.COMMAND, action, session_key, context)
        return self.emit(event)

    def emit_message_received(
        self,
        session_key: str,
        from_: str,
        content: str,
        channel_id: str,
        **kwargs: Any,
    ) -> List[str]:
        """
        Emit a message:received event.

        Args:
            session_key: The session identifier
            from_: Sender identifier
            content: Message content
            channel_id: Channel identifier
            **kwargs: Additional context data

        Returns:
            List of messages from handlers
        """
        context = {
            "from": from_,
            "content": content,
            "channelId": channel_id,
            **kwargs,
        }
        event = self.create_event(HookEventType.MESSAGE, "received", session_key, context)
        return self.emit(event)

    def emit_message_sent(
        self,
        session_key: str,
        to: str,
        content: str,
        success: bool,
        channel_id: str,
        **kwargs: Any,
    ) -> List[str]:
        """
        Emit a message:sent event.

        Args:
            session_key: The session identifier
            to: Recipient identifier
            content: Message content
            success: Whether the send succeeded
            channel_id: Channel identifier
            **kwargs: Additional context data

        Returns:
            List of messages from handlers
        """
        context = {
            "to": to,
            "content": content,
            "success": success,
            "channelId": channel_id,
            **kwargs,
        }
        event = self.create_event(HookEventType.MESSAGE, "sent", session_key, context)
        return self.emit(event)

    def emit_agent_bootstrap(
        self,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit an agent:bootstrap event.

        Args:
            session_key: The session identifier
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.AGENT, "bootstrap", session_key, context)
        return self.emit(event)

    def emit_gateway_startup(
        self,
        session_key: str = "gateway",
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a gateway:startup event.

        Args:
            session_key: The session identifier (defaults to "gateway")
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.GATEWAY, "startup", session_key, context)
        return self.emit(event)

    def emit_middleware_before_agent(
        self,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a middleware:before_agent event.

        Args:
            session_key: The session identifier
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.MIDDLEWARE, "before_agent", session_key, context)
        return self.emit(event)

    def emit_middleware_after_agent(
        self,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a middleware:after_agent event.

        Args:
            session_key: The session identifier
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.MIDDLEWARE, "after_agent", session_key, context)
        return self.emit(event)

    def emit_middleware_before_model(
        self,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a middleware:before_model event.

        Args:
            session_key: The session identifier
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.MIDDLEWARE, "before_model", session_key, context)
        return self.emit(event)

    def emit_middleware_after_model(
        self,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a middleware:after_model event.

        Args:
            session_key: The session identifier
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.MIDDLEWARE, "after_model", session_key, context)
        return self.emit(event)

    def emit_middleware_wrap_tool_call(
        self,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a middleware:wrap_tool_call event.

        Args:
            session_key: The session identifier
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.MIDDLEWARE, "wrap_tool_call", session_key, context)
        return self.emit(event)

    def emit_middleware_wrap_model_call(
        self,
        session_key: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit a middleware:wrap_model_call event.

        Args:
            session_key: The session identifier
            context: Optional context data

        Returns:
            List of messages from handlers
        """
        event = self.create_event(HookEventType.MIDDLEWARE, "wrap_model_call", session_key, context)
        return self.emit(event)

    def get_registered_events(self) -> Set[str]:
        """
        Get all registered event names.

        Returns:
            Set of registered event names
        """
        events = set(self._listeners.keys())
        events.update(f"{t}:*" for t in self._type_listeners.keys())
        if self._wildcard_listeners:
            events.add("*")
        return events

    def get_handler_count(self, event: Optional[str] = None) -> int:
        """
        Get the number of registered handlers.

        Args:
            event: Optional event name to count handlers for

        Returns:
            Number of handlers
        """
        if event is None:
            total = len(self._wildcard_listeners)
            for handlers in self._listeners.values():
                total += len(handlers)
            for handlers in self._type_listeners.values():
                total += len(handlers)
            return total

        count = 0
        if event in self._listeners:
            count += len(self._listeners[event])
        
        if ":" in event:
            event_type = event.split(":")[0]
            if event_type in self._type_listeners:
                count += len(self._type_listeners[event_type])
        
        count += len(self._wildcard_listeners)
        return count

    def clear(self) -> None:
        """Clear all registered handlers."""
        self._listeners.clear()
        self._type_listeners.clear()
        self._wildcard_listeners.clear()
