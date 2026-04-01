"""
Type definitions for the OpenClaw Hooks System.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import os


class HookEventType(str, Enum):
    COMMAND = "command"
    SESSION = "session"
    AGENT = "agent"
    GATEWAY = "gateway"
    MESSAGE = "message"
    MIDDLEWARE = "middleware"


class HookAction(str, Enum):
    NEW = "new"
    RESET = "reset"
    STOP = "stop"
    BOOTSTRAP = "bootstrap"
    STARTUP = "startup"
    RECEIVED = "received"
    SENT = "sent"
    START = "start"
    END = "end"
    ERROR = "error"
    BEFORE_AGENT = "before_agent"
    AFTER_AGENT = "after_agent"
    BEFORE_MODEL = "before_model"
    AFTER_MODEL = "after_model"
    WRAP_TOOL_CALL = "wrap_tool_call"
    WRAP_MODEL_CALL = "wrap_model_call"


@dataclass
class CommandContext:
    session_entry: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    session_file: Optional[str] = None
    command_source: Optional[str] = None
    sender_id: Optional[str] = None
    workspace_dir: Optional[str] = None
    bootstrap_files: Optional[List[Dict[str, Any]]] = None
    cfg: Optional[Dict[str, Any]] = None


@dataclass
class MessageReceivedContext:
    from_: str
    content: str
    channel_id: str
    timestamp: Optional[int] = None
    account_id: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class MessageSentContext:
    to: str
    content: str
    success: bool
    channel_id: str
    error: Optional[str] = None
    account_id: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None


@dataclass
class AgentBootstrapContext:
    workspace_dir: Optional[str] = None
    bootstrap_files: Optional[List[Dict[str, Any]]] = None
    cfg: Optional[Dict[str, Any]] = None


@dataclass
class GatewayStartupContext:
    workspace_dir: Optional[str] = None
    cfg: Optional[Dict[str, Any]] = None


EventContext = Union[
    CommandContext,
    MessageReceivedContext,
    MessageSentContext,
    AgentBootstrapContext,
    GatewayStartupContext,
    Dict[str, Any],
]


@dataclass
class HookEvent:
    type: HookEventType
    action: str
    session_key: str
    timestamp: datetime
    messages: List[str] = field(default_factory=list)
    context: EventContext = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value if isinstance(self.type, HookEventType) else self.type,
            "action": self.action,
            "sessionKey": self.session_key,
            "timestamp": self.timestamp.isoformat(),
            "messages": self.messages,
            "context": self._context_to_dict(),
        }

    def _context_to_dict(self) -> Dict[str, Any]:
        if isinstance(self.context, dict):
            return self.context
        if hasattr(self.context, "__dataclass_fields__"):
            result = {}
            for f in self.context.__dataclass_fields__:
                val = getattr(self.context, f)
                if val is not None:
                    result[f] = val
            return result
        return {}


HookHandler = Callable[[HookEvent], None]


@dataclass
class RequiresConfig:
    bins: Optional[List[str]] = None
    any_bins: Optional[List[str]] = None
    env: Optional[List[str]] = None
    config: Optional[List[str]] = None
    os: Optional[List[str]] = None


@dataclass
class HookMetadata:
    name: str
    description: str
    homepage: Optional[str] = None
    emoji: Optional[str] = None
    events: List[str] = field(default_factory=list)
    export: str = "default"
    requires: Optional[RequiresConfig] = None
    always: bool = False
    install: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, name: str, description: str, data: Dict[str, Any]) -> "HookMetadata":
        metadata_obj = data.get("metadata", {})
        openclaw_data = metadata_obj.get("openclaw", {})
        requires_data = openclaw_data.get("requires", {})
        
        requires = None
        if requires_data:
            requires = RequiresConfig(
                bins=requires_data.get("bins"),
                any_bins=requires_data.get("anyBins"),
                env=requires_data.get("env"),
                config=requires_data.get("config"),
                os=requires_data.get("os"),
            )

        return cls(
            name=name,
            description=description,
            homepage=data.get("homepage"),
            emoji=openclaw_data.get("emoji"),
            events=openclaw_data.get("events", []),
            export=openclaw_data.get("export", "default"),
            requires=requires,
            always=openclaw_data.get("always", False),
            install=openclaw_data.get("install"),
        )


@dataclass
class HookInfo:
    name: str
    description: str
    path: str
    metadata: HookMetadata
    handler_path: Optional[str] = None
    enabled: bool = False
    eligible: bool = True
    eligibility_reasons: List[str] = field(default_factory=list)


@dataclass
class HookEntryConfig:
    enabled: bool = True
    env: Optional[Dict[str, str]] = None
    paths: Optional[List[str]] = None


@dataclass
class HookLoadConfig:
    extra_dirs: Optional[List[str]] = None


@dataclass
class HookConfig:
    enabled: bool = True
    entries: Dict[str, HookEntryConfig] = field(default_factory=dict)
    load: Optional[HookLoadConfig] = None
    handlers: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HookConfig":
        internal = data.get("internal", {})
        entries = {}
        
        for name, entry_data in internal.get("entries", {}).items():
            if isinstance(entry_data, bool):
                entries[name] = HookEntryConfig(enabled=entry_data)
            elif isinstance(entry_data, dict):
                entries[name] = HookEntryConfig(
                    enabled=entry_data.get("enabled", True),
                    env=entry_data.get("env"),
                    paths=entry_data.get("paths"),
                )
        
        load_config = None
        if "load" in internal:
            load_data = internal["load"]
            load_config = HookLoadConfig(extra_dirs=load_data.get("extraDirs"))

        return cls(
            enabled=internal.get("enabled", True),
            entries=entries,
            load=load_config,
            handlers=internal.get("handlers"),
        )


@dataclass
class EligibilityResult:
    eligible: bool
    reasons: List[str] = field(default_factory=list)
    missing_bins: List[str] = field(default_factory=list)
    missing_env: List[str] = field(default_factory=list)
    missing_config: List[str] = field(default_factory=list)
    os_mismatch: bool = False


@dataclass
class HookStatus:
    name: str
    enabled: bool
    eligible: bool
    emoji: Optional[str] = None
    description: Optional[str] = None
    events: List[str] = field(default_factory=list)
    path: Optional[str] = None
    eligibility_reasons: List[str] = field(default_factory=list)


def get_default_hooks_dir() -> str:
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(hook_dir, "bundled_hooks")


def get_default_workspace_dir() -> str:
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(hook_dir, "workspace")


def get_default_logs_dir() -> str:
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(hook_dir, "workspace", "logs")
