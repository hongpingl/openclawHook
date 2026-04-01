"""
CLI commands for the OpenClaw Hooks System.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from .manager import HookManager
from .hook_types import HookStatus, get_default_hooks_dir, get_default_workspace_dir


class HooksCLI:
    """Command-line interface for managing hooks."""

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.workspace_dir = workspace_dir or get_default_workspace_dir()
        self.manager = HookManager(workspace_dir=self.workspace_dir, config=config)

    def list_hooks(
        self,
        eligible_only: bool = False,
        verbose: bool = False,
        json_output: bool = False,
    ) -> None:
        """
        List all discovered hooks.

        Args:
            eligible_only: Only show eligible hooks
            verbose: Show detailed information
            json_output: Output as JSON
        """
        self.manager.initialize()
        statuses = self.manager.get_status()

        if eligible_only:
            statuses = [s for s in statuses if s.eligible]

        if json_output:
            output = []
            for s in statuses:
                output.append({
                    "name": s.name,
                    "enabled": s.enabled,
                    "eligible": s.eligible,
                    "emoji": s.emoji,
                    "description": s.description,
                    "events": s.events,
                    "path": s.path,
                })
            print(json.dumps(output, indent=2))
            return

        if not statuses:
            print("No hooks discovered.")
            return

        for status in statuses:
            self._print_hook_status(status, verbose)

    def _print_hook_status(self, status: HookStatus, verbose: bool) -> None:
        """Print a single hook status."""
        emoji = status.emoji or "  "
        enabled_mark = "✓" if status.enabled else " "
        eligible_mark = "" if status.eligible else " (ineligible)"

        print(f"{emoji} {status.name} [{enabled_mark}]{eligible_mark}")

        if verbose:
            print(f"    Description: {status.description}")
            print(f"    Events: {', '.join(status.events) if status.events else 'none'}")
            print(f"    Path: {status.path}")
            
            if not status.eligible and status.eligibility_reasons:
                print(f"    Missing requirements:")
                for reason in status.eligibility_reasons:
                    print(f"      - {reason}")
            print()

    def show_info(self, name: str, json_output: bool = False) -> None:
        """
        Show detailed information about a hook.

        Args:
            name: The hook name
            json_output: Output as JSON
        """
        self.manager.initialize()
        hook_info = self.manager.get_hook(name)

        if hook_info is None:
            print(f"Hook not found: {name}")
            return

        eligibility = self.manager.check_eligibility(name)

        if json_output:
            output = {
                "name": hook_info.name,
                "description": hook_info.description,
                "path": hook_info.path,
                "handler_path": hook_info.handler_path,
                "enabled": hook_info.enabled,
                "eligible": hook_info.eligible,
                "metadata": {
                    "emoji": hook_info.metadata.emoji,
                    "events": hook_info.metadata.events,
                    "export": hook_info.metadata.export,
                    "homepage": hook_info.metadata.homepage,
                },
                "eligibility": eligibility,
            }
            print(json.dumps(output, indent=2))
            return

        emoji = hook_info.metadata.emoji or "  "
        print(f"{emoji} {hook_info.name}")
        print(f"  Description: {hook_info.description}")
        print(f"  Path: {hook_info.path}")
        print(f"  Handler: {hook_info.handler_path or 'not found'}")
        print(f"  Enabled: {hook_info.enabled}")
        print(f"  Eligible: {hook_info.eligible}")
        print(f"  Events: {', '.join(hook_info.metadata.events) if hook_info.metadata.events else 'none'}")

        if hook_info.metadata.homepage:
            print(f"  Homepage: {hook_info.metadata.homepage}")

        if eligibility and not eligibility.get("eligible"):
            print("  Missing requirements:")
            for reason in eligibility.get("reasons", []):
                print(f"    - {reason}")

    def check_eligibility(self, json_output: bool = False) -> None:
        """
        Check eligibility for all hooks.

        Args:
            json_output: Output as JSON
        """
        self.manager.initialize()
        statuses = self.manager.get_status()

        if json_output:
            output = []
            for s in statuses:
                eligibility = self.manager.check_eligibility(s.name)
                output.append({
                    "name": s.name,
                    "eligible": s.eligible,
                    "reasons": eligibility.get("reasons", []) if eligibility else [],
                })
            print(json.dumps(output, indent=2))
            return

        eligible_count = sum(1 for s in statuses if s.eligible)
        total_count = len(statuses)

        print(f"Eligibility check: {eligible_count}/{total_count} hooks eligible")
        print()

        for status in statuses:
            emoji = status.emoji or "  "
            mark = "✓" if status.eligible else "✗"
            print(f"{emoji} {status.name} [{mark}]")

            if not status.eligible and status.eligibility_reasons:
                for reason in status.eligibility_reasons:
                    print(f"    - {reason}")

    def enable_hook(self, name: str) -> None:
        """
        Enable a hook.

        Args:
            name: The hook name
        """
        self.manager.initialize()

        hook_info = self.manager.get_hook(name)
        if hook_info is None:
            print(f"Hook not found: {name}")
            return

        if not hook_info.eligible:
            print(f"Hook '{name}' is not eligible. Run 'openclaw hooks info {name}' for details.")
            return

        if self.manager.enable_hook(name):
            print(f"Hook '{name}' enabled.")
        else:
            print(f"Failed to enable hook '{name}'.")

    def disable_hook(self, name: str) -> None:
        """
        Disable a hook.

        Args:
            name: The hook name
        """
        self.manager.initialize()

        hook_info = self.manager.get_hook(name)
        if hook_info is None:
            print(f"Hook not found: {name}")
            return

        if self.manager.disable_hook(name):
            print(f"Hook '{name}' disabled.")
        else:
            print(f"Failed to disable hook '{name}'.")

    def create_hook(
        self,
        name: str,
        description: str,
        events: List[str],
        emoji: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> None:
        """
        Create a new hook.

        Args:
            name: Hook name
            description: Hook description
            events: List of events
            emoji: Optional emoji
            directory: Optional parent directory
        """
        hook_path = self.manager.create_hook(
            name=name,
            description=description,
            events=events,
            directory=directory,
            emoji=emoji,
        )

        if hook_path:
            print(f"Hook '{name}' created at: {hook_path}")
        else:
            print(f"Failed to create hook '{name}'.")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the hooks CLI."""
    parser = argparse.ArgumentParser(
        prog="openclaw hooks",
        description="Manage OpenClaw hooks",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    list_parser = subparsers.add_parser("list", help="List all hooks")
    list_parser.add_argument("--eligible", action="store_true", help="Show only eligible hooks")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")

    info_parser = subparsers.add_parser("info", help="Show hook details")
    info_parser.add_argument("name", help="Hook name")
    info_parser.add_argument("--json", action="store_true", help="Output as JSON")

    check_parser = subparsers.add_parser("check", help="Check hook eligibility")
    check_parser.add_argument("--json", action="store_true", help="Output as JSON")

    enable_parser = subparsers.add_parser("enable", help="Enable a hook")
    enable_parser.add_argument("name", help="Hook name")

    disable_parser = subparsers.add_parser("disable", help="Disable a hook")
    disable_parser.add_argument("name", help="Hook name")

    create_parser = subparsers.add_parser("create", help="Create a new hook")
    create_parser.add_argument("name", help="Hook name")
    create_parser.add_argument("--description", "-d", required=True, help="Hook description")
    create_parser.add_argument("--events", "-e", required=True, nargs="+", help="Events to listen for")
    create_parser.add_argument("--emoji", help="Emoji for the hook")
    create_parser.add_argument("--directory", help="Parent directory for the hook")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the hooks CLI.

    Args:
        args: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.command is None:
        parser.print_help()
        return 0

    workspace_dir = os.environ.get("OPENCLAW_WORKSPACE_DIR")
    cli = HooksCLI(workspace_dir=workspace_dir)

    if parsed_args.command == "list":
        cli.list_hooks(
            eligible_only=parsed_args.eligible,
            verbose=parsed_args.verbose,
            json_output=parsed_args.json,
        )
    elif parsed_args.command == "info":
        cli.show_info(parsed_args.name, json_output=parsed_args.json)
    elif parsed_args.command == "check":
        cli.check_eligibility(json_output=parsed_args.json)
    elif parsed_args.command == "enable":
        cli.enable_hook(parsed_args.name)
    elif parsed_args.command == "disable":
        cli.disable_hook(parsed_args.name)
    elif parsed_args.command == "create":
        cli.create_hook(
            name=parsed_args.name,
            description=parsed_args.description,
            events=parsed_args.events,
            emoji=parsed_args.emoji,
            directory=parsed_args.directory,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
