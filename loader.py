"""
Dynamic module loader for the OpenClaw Hooks System.
"""

import importlib.util
import os
import sys
from typing import Any, Callable, Dict, List, Optional

from .hook_types import HookHandler, HookInfo


class HandlerLoader:
    """
    Dynamically loads hook handlers from Python modules.
    """

    def __init__(self):
        self._loaded_handlers: Dict[str, HookHandler] = {}
        self._loaded_modules: Dict[str, Any] = {}

    def load_handler(self, hook_info: HookInfo) -> Optional[HookHandler]:
        """
        Load a handler from a hook.

        Args:
            hook_info: The hook information

        Returns:
            The loaded handler function, or None if loading failed
        """
        if hook_info.name in self._loaded_handlers:
            return self._loaded_handlers[hook_info.name]

        if not hook_info.handler_path:
            return None

        if not os.path.isfile(hook_info.handler_path):
            return None

        try:
            module = self._load_module(hook_info.handler_path, hook_info.name)
            if module is None:
                return None

            export_name = hook_info.metadata.export
            handler = self._get_export(module, export_name)

            if handler is None:
                return None

            if not callable(handler):
                return None

            self._loaded_handlers[hook_info.name] = handler
            self._loaded_modules[hook_info.name] = module

            return handler

        except Exception as e:
            print(f"[HandlerLoader] Error loading handler for {hook_info.name}: {e}")
            return None

    def _load_module(self, path: str, name: str) -> Optional[Any]:
        """
        Load a Python module from a file path.

        Args:
            path: Path to the Python file
            name: Module name to use

        Returns:
            The loaded module, or None if loading failed
        """
        module_name = f"openclaw_hook_{name.replace('-', '_')}"

        if module_name in sys.modules:
            return sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            del sys.modules[module_name]
            print(f"[HandlerLoader] Error executing module {module_name}: {e}")
            return None

    def _get_export(self, module: Any, export_name: str) -> Optional[Callable]:
        """
        Get an exported function from a module.

        Args:
            module: The loaded module
            export_name: The name of the export

        Returns:
            The exported function, or None if not found
        """
        if export_name == "default":
            if hasattr(module, "export"):
                return getattr(module, "export")
            if hasattr(module, "handler"):
                return getattr(module, "handler")
            if hasattr(module, "default"):
                return getattr(module, "default")
            for attr_name in dir(module):
                if attr_name.startswith("_"):
                    continue
                attr = getattr(module, attr_name)
                if callable(attr):
                    return attr
            return None

        return getattr(module, export_name, None)

    def load_handlers(self, hooks: List[HookInfo]) -> Dict[str, HookHandler]:
        """
        Load handlers for multiple hooks.

        Args:
            hooks: List of hook information

        Returns:
            Dictionary mapping hook names to handlers
        """
        handlers = {}
        for hook_info in hooks:
            handler = self.load_handler(hook_info)
            if handler:
                handlers[hook_info.name] = handler
        return handlers

    def unload_handler(self, name: str) -> bool:
        """
        Unload a handler by name.

        Args:
            name: The hook name

        Returns:
            True if the handler was unloaded, False if it wasn't loaded
        """
        if name in self._loaded_handlers:
            del self._loaded_handlers[name]
            
            module_name = f"openclaw_hook_{name.replace('-', '_')}"
            if module_name in sys.modules:
                del sys.modules[module_name]
            if name in self._loaded_modules:
                del self._loaded_modules[name]
            
            return True
        return False

    def reload_handler(self, hook_info: HookInfo) -> Optional[HookHandler]:
        """
        Reload a handler, forcing a fresh load.

        Args:
            hook_info: The hook information

        Returns:
            The reloaded handler, or None if loading failed
        """
        self.unload_handler(hook_info.name)
        return self.load_handler(hook_info)

    def is_loaded(self, name: str) -> bool:
        """
        Check if a handler is loaded.

        Args:
            name: The hook name

        Returns:
            True if the handler is loaded, False otherwise
        """
        return name in self._loaded_handlers

    def get_loaded_handlers(self) -> Dict[str, HookHandler]:
        """
        Get all loaded handlers.

        Returns:
            Dictionary of all loaded handlers
        """
        return self._loaded_handlers.copy()

    def clear_all(self) -> None:
        """Clear all loaded handlers and modules."""
        for name in list(self._loaded_handlers.keys()):
            self.unload_handler(name)


class LegacyHandlerLoader:
    """
    Loader for legacy handlers defined in config.
    """

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = workspace_dir
        self._loader = HandlerLoader()

    def load_legacy_handlers(
        self, handlers_config: List[Dict[str, Any]]
    ) -> Dict[str, List[HookHandler]]:
        """
        Load legacy handlers from config.

        Args:
            handlers_config: List of legacy handler configurations

        Returns:
            Dictionary mapping event names to lists of handlers
        """
        handlers_by_event: Dict[str, List[HookHandler]] = {}

        for config in handlers_config:
            event = config.get("event")
            module_path = config.get("module")
            export = config.get("export", "default")

            if not event or not module_path:
                continue

            if self.workspace_dir:
                if module_path.startswith("./"):
                    module_path = os.path.join(self.workspace_dir, module_path)
                elif not os.path.isabs(module_path):
                    module_path = os.path.join(self.workspace_dir, module_path)

            real_path = os.path.realpath(module_path)
            real_workspace = os.path.realpath(self.workspace_dir) if self.workspace_dir else ""

            if self.workspace_dir and not real_path.startswith(real_workspace):
                print(f"[LegacyHandlerLoader] Module path escapes workspace: {module_path}")
                continue

            if not os.path.isfile(module_path):
                print(f"[LegacyHandlerLoader] Module file not found: {module_path}")
                continue

            from AutoSAR_Agent.hook.hook_types import HookInfo, HookMetadata
            
            metadata = HookMetadata(
                name=f"legacy_{event}_{module_path}",
                description="Legacy handler",
                events=[event],
                export=export,
            )
            
            hook_info = HookInfo(
                name=metadata.name,
                description=metadata.description,
                path=os.path.dirname(module_path),
                metadata=metadata,
                handler_path=module_path,
            )

            handler = self._loader.load_handler(hook_info)
            if handler:
                if event not in handlers_by_event:
                    handlers_by_event[event] = []
                handlers_by_event[event].append(handler)

        return handlers_by_event
