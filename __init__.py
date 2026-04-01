"""
OpenClaw Hooks System
"""

from .hook_types import (
    HookConfig,
    HookEvent,
    HookEventType,
    HookHandler,
    HookInfo,
    HookMetadata,
    HookStatus,
    get_default_hooks_dir,
    get_default_workspace_dir,
    get_default_logs_dir,
)
from .manager import HookManager
from .discovery import HookDiscovery
from .emitter import EventEmitter
from .loader import HandlerLoader
from .eligibility import EligibilityChecker

__all__ = [
    "HookConfig",
    "HookEvent",
    "HookEventType",
    "HookHandler",
    "HookInfo",
    "HookMetadata",
    "HookStatus",
    "HookManager",
    "HookDiscovery",
    "EventEmitter",
    "HandlerLoader",
    "EligibilityChecker",
    "get_default_hooks_dir",
    "get_default_workspace_dir",
    "get_default_logs_dir",
]
