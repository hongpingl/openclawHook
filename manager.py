"""
Hook manager for the OpenClaw Hooks System.
"""

import json
import os
from typing import Any, Dict, List, Optional

from .discovery import HookDiscovery
from .eligibility import EligibilityChecker
from .emitter import EventEmitter
from .loader import HandlerLoader, LegacyHandlerLoader
from .hook_types import (
    HookConfig,
    HookEntryConfig,
    HookEvent,
    HookHandler,
    HookInfo,
    HookStatus,
    get_default_hooks_dir,
)


class HookManager:
    """
    Central manager for the OpenClaw hooks system.
    
    Handles discovery, loading, eligibility checking, and event emission.
    """

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        managed_hooks_dir: Optional[str] = None,
        bundled_hooks_dir: Optional[str] = None,
    ):
        self.workspace_dir = workspace_dir
        self.config = config or {}
        
        self._hook_config = HookConfig.from_dict(self.config.get("hooks", {}))
        
        extra_dirs = None
        if self._hook_config.load and self._hook_config.load.extra_dirs:
            extra_dirs = self._hook_config.load.extra_dirs

        self.discovery = HookDiscovery(
            workspace_dir=workspace_dir,
            managed_hooks_dir=managed_hooks_dir or get_default_hooks_dir(),
            bundled_hooks_dir=bundled_hooks_dir,
            extra_dirs=extra_dirs,
        )

        self.eligibility_checker = EligibilityChecker(self.config)
        self.loader = HandlerLoader()
        self.emitter = EventEmitter()

        self._hooks: Dict[str, HookInfo] = {}
        self._enabled_hooks: Dict[str, HookInfo] = {}
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize the hook manager by discovering and loading hooks.
        """
        if self._initialized:
            return

        if not self._hook_config.enabled:
            self._initialized = True
            return

        self._hooks = self.discovery.discover_all()

        for name, hook_info in self._hooks.items():
            eligibility = self.eligibility_checker.check(hook_info.metadata)
            hook_info.eligible = eligibility.eligible
            hook_info.eligibility_reasons = eligibility.reasons

            entry_config = self._hook_config.entries.get(name)
            if entry_config:
                hook_info.enabled = entry_config.enabled
            else:
                hook_info.enabled = False

            if hook_info.enabled and hook_info.eligible:
                self._enabled_hooks[name] = hook_info
                self._register_hook(hook_info)

        if self._hook_config.handlers:
            self._load_legacy_handlers()

        self._initialized = True

    def _register_hook(self, hook_info: HookInfo) -> None:
        """
        Register a hook's handler with the event emitter.

        Args:
            hook_info: The hook information
        """
        handler = self.loader.load_handler(hook_info)
        if handler is None:
            return

        for event in hook_info.metadata.events:
            if ":" in event:
                self.emitter.on(event, handler)
            else:
                self.emitter.on_type(event, handler)

    def _load_legacy_handlers(self) -> None:
        """Load legacy handlers from config."""
        if not self._hook_config.handlers:
            return

        legacy_loader = LegacyHandlerLoader(self.workspace_dir)
        handlers_by_event = legacy_loader.load_legacy_handlers(self._hook_config.handlers)

        for event, handlers in handlers_by_event.items():
            for handler in handlers:
                if ":" in event:
                    self.emitter.on(event, handler)
                else:
                    self.emitter.on_type(event, handler)

    def reload(self) -> None:
        """Reload all hooks."""
        self._initialized = False
        self._hooks.clear()
        self._enabled_hooks.clear()
        self.emitter.clear()
        self.loader.clear_all()
        self.initialize()

    def get_hooks(self) -> Dict[str, HookInfo]:
        """
        Get all discovered hooks.

        Returns:
            Dictionary of all hooks
        """
        if not self._initialized:
            self.initialize()
        return self._hooks

    def get_enabled_hooks(self) -> Dict[str, HookInfo]:
        """
        Get all enabled hooks.

        Returns:
            Dictionary of enabled hooks
        """
        if not self._initialized:
            self.initialize()
        return self._enabled_hooks

    def get_hook(self, name: str) -> Optional[HookInfo]:
        """
        Get a specific hook by name.

        Args:
            name: The hook name

        Returns:
            HookInfo if found, None otherwise
        """
        if not self._initialized:
            self.initialize()
        return self._hooks.get(name)

    def enable_hook(self, name: str) -> bool:
        """
        Enable a hook.

        Args:
            name: The hook name

        Returns:
            True if enabled, False if not found or ineligible
        """
        if not self._initialized:
            self.initialize()

        hook_info = self._hooks.get(name)
        if hook_info is None:
            return False

        if not hook_info.eligible:
            return False

        hook_info.enabled = True
        self._enabled_hooks[name] = hook_info
        self._register_hook(hook_info)

        return True

    def disable_hook(self, name: str) -> bool:
        """
        Disable a hook.

        Args:
            name: The hook name

        Returns:
            True if disabled, False if not found
        """
        if not self._initialized:
            self.initialize()

        hook_info = self._hooks.get(name)
        if hook_info is None:
            return False

        hook_info.enabled = False

        if name in self._enabled_hooks:
            del self._enabled_hooks[name]

        return True

    def emit(self, event: HookEvent) -> List[str]:
        """
        Emit an event to all registered handlers.

        Args:
            event: The event to emit

        Returns:
            List of messages from handlers
        """
        if not self._initialized:
            self.initialize()
        return self.emitter.emit(event)

    async def emit_async(self, event: HookEvent) -> List[str]:
        """
        Emit an event asynchronously.

        Args:
            event: The event to emit

        Returns:
            List of messages from handlers
        """
        if not self._initialized:
            self.initialize()
        return await self.emitter.emit_async(event)

    def get_status(self) -> List[HookStatus]:
        """
        Get the status of all hooks.

        Returns:
            List of hook statuses
        """
        if not self._initialized:
            self.initialize()

        statuses = []
        for name, hook_info in self._hooks.items():
            status = HookStatus(
                name=name,
                enabled=hook_info.enabled,
                eligible=hook_info.eligible,
                emoji=hook_info.metadata.emoji,
                description=hook_info.description,
                events=hook_info.metadata.events,
                path=hook_info.path,
                eligibility_reasons=hook_info.eligibility_reasons,
            )
            statuses.append(status)

        return statuses

    def get_status_dict(self) -> List[Dict[str, Any]]:
        """
        Get the status of all hooks as dictionaries.

        Returns:
            List of hook status dictionaries
        """
        statuses = self.get_status()
        return [
            {
                "name": s.name,
                "enabled": s.enabled,
                "eligible": s.eligible,
                "emoji": s.emoji,
                "description": s.description,
                "events": s.events,
                "path": s.path,
                "eligibility_reasons": s.eligibility_reasons,
            }
            for s in statuses
        ]

    def check_eligibility(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Check eligibility for a specific hook.

        Args:
            name: The hook name

        Returns:
            Eligibility result dictionary, or None if hook not found
        """
        if not self._initialized:
            self.initialize()

        hook_info = self._hooks.get(name)
        if hook_info is None:
            return None

        result = self.eligibility_checker.check(hook_info.metadata)
        return {
            "name": name,
            "eligible": result.eligible,
            "reasons": result.reasons,
            "missing_bins": result.missing_bins,
            "missing_env": result.missing_env,
            "missing_config": result.missing_config,
            "os_mismatch": result.os_mismatch,
        }

    def create_hook(
        self,
        name: str,
        description: str,
        events: List[str],
        directory: Optional[str] = None,
        emoji: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a new hook.

        Args:
            name: Hook name
            description: Hook description
            events: List of events the hook listens for
            directory: Parent directory (defaults to managed hooks dir)
            emoji: Optional emoji for the hook

        Returns:
            Path to the created hook directory, or None on failure
        """
        try:
            hook_path = self.discovery.create_hook_directory(
                name=name,
                description=description,
                events=events,
                directory=directory,
                emoji=emoji,
            )
            return hook_path
        except Exception as e:
            print(f"[HookManager] Error creating hook: {e}")
            return None

    def save_config(self, path: Optional[str] = None) -> bool:
        """
        Save the current hook configuration.

        Args:
            path: Path to save config (defaults to workspace config)

        Returns:
            True if saved successfully, False otherwise
        """
        if path is None:
            if self.workspace_dir:
                path = os.path.join(self.workspace_dir, "config.json")
            else:
                return False

        try:
            config_data = self.config.copy()
            
            entries = {}
            for name, hook_info in self._hooks.items():
                entries[name] = {"enabled": hook_info.enabled}
            
            config_data["hooks"] = {
                "internal": {
                    "enabled": self._hook_config.enabled,
                    "entries": entries,
                }
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            return True
        except Exception as e:
            print(f"[HookManager] Error saving config: {e}")
            return False

    def load_config(self, path: str) -> bool:
        """
        Load hook configuration from a file.

        Args:
            path: Path to the config file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            self.config = config_data
            self._hook_config = HookConfig.from_dict(config_data.get("hooks", {}))
            
            self.reload()
            return True
        except Exception as e:
            print(f"[HookManager] Error loading config: {e}")
            return False

    def get_event_emitter(self) -> EventEmitter:
        """
        Get the event emitter for direct use.

        Returns:
            The EventEmitter instance
        """
        return self.emitter

    def is_initialized(self) -> bool:
        """
        Check if the manager has been initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
