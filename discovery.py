"""
Hook discovery system for the OpenClaw Hooks System.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .hook_types import HookInfo, HookMetadata, get_default_hooks_dir
from .frontmatter import parse_hook_md


class HookDiscovery:
    """
    Discovers hooks from multiple directories in order of precedence:
    1. Workspace hooks: <workspace>/hooks/ (per-agent, highest precedence)
    2. Managed hooks: ~/.openclaw/hooks/ (user-installed, shared across workspaces)
    3. Bundled hooks: <openclaw>/dist/hooks/bundled/ (shipped with OpenClaw)
    """

    HOOK_MD_FILE = "HOOK.md"
    HANDLER_FILES = ["handler.py", "handler.ts", "index.py", "index.ts"]

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        managed_hooks_dir: Optional[str] = None,
        bundled_hooks_dir: Optional[str] = None,
        extra_dirs: Optional[List[str]] = None,
    ):
        self.workspace_dir = workspace_dir
        self.managed_hooks_dir = managed_hooks_dir or get_default_hooks_dir()
        self.bundled_hooks_dir = bundled_hooks_dir
        self.extra_dirs = extra_dirs or []
        
        self._discovered_hooks: Dict[str, HookInfo] = {}
        self._discovery_order: List[str] = []

    def discover_all(self) -> Dict[str, HookInfo]:
        """
        Discover all hooks from all configured directories.

        Returns:
            Dictionary mapping hook names to HookInfo objects
        """
        self._discovered_hooks = {}
        self._discovery_order = []

        directories = self._get_discovery_directories()

        for directory in directories:
            self._discover_from_directory(directory)

        return self._discovered_hooks

    def _get_discovery_directories(self) -> List[str]:
        """Get the list of directories to scan for hooks."""
        directories = []

        if self.workspace_dir:
            workspace_hooks = os.path.join(self.workspace_dir, "hooks")
            directories.append(workspace_hooks)

        directories.append(self.managed_hooks_dir)

        if self.bundled_hooks_dir:
            directories.append(self.bundled_hooks_dir)

        directories.extend(self.extra_dirs)

        return directories

    def _discover_from_directory(self, directory: str) -> None:
        """
        Discover hooks from a single directory.

        Args:
            directory: Path to the directory to scan
        """
        if not os.path.isdir(directory):
            return

        for entry in os.listdir(directory):
            hook_path = os.path.join(directory, entry)

            if not os.path.isdir(hook_path):
                continue

            hook_info = self._load_hook_info(hook_path)
            if hook_info:
                if hook_info.name not in self._discovered_hooks:
                    self._discovered_hooks[hook_info.name] = hook_info
                    self._discovery_order.append(hook_info.name)

    def _load_hook_info(self, hook_path: str) -> Optional[HookInfo]:
        """
        Load hook information from a hook directory.

        Args:
            hook_path: Path to the hook directory

        Returns:
            HookInfo if valid hook, None otherwise
        """
        hook_md_path = os.path.join(hook_path, self.HOOK_MD_FILE)

        if not os.path.isfile(hook_md_path):
            return None

        try:
            with open(hook_md_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (IOError, OSError):
            return None

        metadata, _ = parse_hook_md(content)

        if metadata is None:
            return None

        handler_path = self._find_handler(hook_path)

        return HookInfo(
            name=metadata.name,
            description=metadata.description,
            path=hook_path,
            metadata=metadata,
            handler_path=handler_path,
        )

    def _find_handler(self, hook_path: str) -> Optional[str]:
        """
        Find the handler file in a hook directory.

        Args:
            hook_path: Path to the hook directory

        Returns:
            Path to the handler file, or None if not found
        """
        for handler_file in self.HANDLER_FILES:
            handler_path = os.path.join(hook_path, handler_file)
            if os.path.isfile(handler_path):
                return handler_path
        return None

    def get_hook(self, name: str) -> Optional[HookInfo]:
        """
        Get a specific hook by name.

        Args:
            name: The hook name

        Returns:
            HookInfo if found, None otherwise
        """
        return self._discovered_hooks.get(name)

    def get_all_hooks(self) -> Dict[str, HookInfo]:
        """
        Get all discovered hooks.

        Returns:
            Dictionary of all discovered hooks
        """
        if not self._discovered_hooks:
            self.discover_all()
        return self._discovered_hooks

    def get_discovery_order(self) -> List[str]:
        """
        Get the order in which hooks were discovered.

        Returns:
            List of hook names in discovery order
        """
        return self._discovery_order.copy()

    def is_hook_pack(self, directory: str) -> bool:
        """
        Check if a directory is a hook pack (npm package).

        Args:
            directory: Path to check

        Returns:
            True if it's a hook pack, False otherwise
        """
        package_json_path = os.path.join(directory, "package.json")
        if not os.path.isfile(package_json_path):
            return False

        try:
            import json
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_data = json.load(f)
            
            openclaw_config = package_data.get("openclaw", {})
            hooks = openclaw_config.get("hooks", [])
            return bool(hooks)
        except (IOError, OSError, json.JSONDecodeError):
            return False

    def discover_hook_pack(self, directory: str) -> List[HookInfo]:
        """
        Discover hooks from a hook pack directory.

        Args:
            directory: Path to the hook pack

        Returns:
            List of HookInfo objects from the pack
        """
        hooks = []
        package_json_path = os.path.join(directory, "package.json")

        if not os.path.isfile(package_json_path):
            return hooks

        try:
            import json
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_data = json.load(f)
        except (IOError, OSError, json.JSONDecodeError):
            return hooks

        openclaw_config = package_data.get("openclaw", {})
        hook_entries = openclaw_config.get("hooks", [])

        for entry in hook_entries:
            hook_path = os.path.join(directory, entry)
            
            real_path = os.path.realpath(hook_path)
            real_base = os.path.realpath(directory)
            
            if not real_path.startswith(real_base):
                continue

            hook_info = self._load_hook_info(hook_path)
            if hook_info:
                hooks.append(hook_info)

        return hooks

    def create_hook_directory(
        self,
        name: str,
        description: str,
        events: List[str],
        directory: Optional[str] = None,
        emoji: Optional[str] = None,
    ) -> str:
        """
        Create a new hook directory structure.

        Args:
            name: Hook name
            description: Hook description
            events: List of events the hook listens for
            directory: Parent directory (defaults to managed hooks dir)
            emoji: Optional emoji for the hook

        Returns:
            Path to the created hook directory
        """
        if directory is None:
            directory = self.managed_hooks_dir

        hook_path = os.path.join(directory, name)
        os.makedirs(hook_path, exist_ok=True)

        metadata = HookMetadata(
            name=name,
            description=description,
            emoji=emoji,
            events=events,
        )

        from .frontmatter import create_hook_md
        
        hook_md_content = create_hook_md(metadata, f"# {name}\n\n{description}")
        hook_md_path = os.path.join(hook_path, self.HOOK_MD_FILE)

        with open(hook_md_path, "w", encoding="utf-8") as f:
            f.write(hook_md_content)

        handler_path = os.path.join(hook_path, "handler.py")
        handler_content = self._generate_handler_template(name, events)
        
        with open(handler_path, "w", encoding="utf-8") as f:
            f.write(handler_content)

        return hook_path

    def _generate_handler_template(self, name: str, events: List[str]) -> str:
        """Generate a handler template for a new hook."""
        events_str = ", ".join(f'"{e}"' for e in events)
        
        return f'''"""
Handler for the {name} hook.
"""

from AutoSAR_Agent.hook.hook_types import HookEvent


def handler(event: HookEvent) -> None:
    """
    Handle hook events.
    
    Args:
        event: The hook event
    """
    if event.type not in [{events_str}]:
        return
    
    print("[{name}] Triggered:", event.type, event.action)
    
    pass


export = handler
'''
