"""
Eligibility checking system for the OpenClaw Hooks System.
"""

import os
import platform
import shutil
from typing import Any, Dict, List, Optional

from .hook_types import EligibilityResult, HookMetadata, RequiresConfig


class EligibilityChecker:
    """
    Checks if a hook is eligible to run based on its requirements.
    
    Requirements can include:
    - bins: Required binaries on PATH
    - anyBins: At least one of these binaries must be present
    - env: Required environment variables
    - config: Required config paths
    - os: Required platforms
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the eligibility checker.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    def check(self, metadata: HookMetadata) -> EligibilityResult:
        """
        Check if a hook is eligible based on its metadata.

        Args:
            metadata: The hook metadata to check

        Returns:
            EligibilityResult with eligibility status and reasons
        """
        if metadata.always:
            return EligibilityResult(eligible=True)

        if metadata.requires is None:
            return EligibilityResult(eligible=True)

        result = EligibilityResult(eligible=True)

        self._check_bins(metadata.requires, result)
        self._check_any_bins(metadata.requires, result)
        self._check_env(metadata.requires, result)
        self._check_config(metadata.requires, result)
        self._check_os(metadata.requires, result)

        result.eligible = (
            len(result.missing_bins) == 0
            and len(result.missing_env) == 0
            and len(result.missing_config) == 0
            and not result.os_mismatch
        )

        if not result.eligible:
            result.reasons = self._build_reasons(result)

        return result

    def _check_bins(self, requires: RequiresConfig, result: EligibilityResult) -> None:
        """Check if all required binaries are available on PATH."""
        if not requires.bins:
            return

        for binary in requires.bins:
            if not self._find_binary(binary):
                result.missing_bins.append(binary)

    def _check_any_bins(self, requires: RequiresConfig, result: EligibilityResult) -> None:
        """Check if at least one of the anyBins is available."""
        if not requires.any_bins:
            return

        found = False
        for binary in requires.any_bins:
            if self._find_binary(binary):
                found = True
                break

        if not found:
            result.missing_bins.extend(requires.any_bins)

    def _check_env(self, requires: RequiresConfig, result: EligibilityResult) -> None:
        """Check if all required environment variables are set."""
        if not requires.env:
            return

        for env_var in requires.env:
            if not os.environ.get(env_var):
                result.missing_env.append(env_var)

    def _check_config(self, requires: RequiresConfig, result: EligibilityResult) -> None:
        """Check if all required config paths are set."""
        if not requires.config:
            return

        for config_path in requires.config:
            if not self._get_config_value(config_path):
                result.missing_config.append(config_path)

    def _check_os(self, requires: RequiresConfig, result: EligibilityResult) -> None:
        """Check if the current OS is supported."""
        if not requires.os:
            return

        current_os = self._get_current_os()
        if current_os not in requires.os:
            result.os_mismatch = True

    def _find_binary(self, binary: str) -> bool:
        """Check if a binary is available on PATH."""
        return shutil.which(binary) is not None

    def _get_config_value(self, path: str) -> Optional[Any]:
        """
        Get a config value by dot-notation path.

        Args:
            path: Dot-notation path (e.g., "workspace.dir")

        Returns:
            The config value, or None if not found
        """
        parts = path.split(".")
        value = self.config

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

            if value is None:
                return None

        return value

    def _get_current_os(self) -> str:
        """Get the current OS identifier."""
        system = platform.system().lower()
        
        os_map = {
            "darwin": "darwin",
            "linux": "linux",
            "windows": "windows",
        }
        
        return os_map.get(system, system)

    def _build_reasons(self, result: EligibilityResult) -> List[str]:
        """Build a list of human-readable reasons for ineligibility."""
        reasons = []

        if result.missing_bins:
            bins_str = ", ".join(result.missing_bins)
            reasons.append(f"Missing required binaries: {bins_str}")

        if result.missing_env:
            env_str = ", ".join(result.missing_env)
            reasons.append(f"Missing required environment variables: {env_str}")

        if result.missing_config:
            config_str = ", ".join(result.missing_config)
            reasons.append(f"Missing required config: {config_str}")

        if result.os_mismatch:
            reasons.append(f"OS not supported (current: {self._get_current_os()})")

        return reasons

    def check_multiple(self, hooks: List[HookMetadata]) -> Dict[str, EligibilityResult]:
        """
        Check eligibility for multiple hooks.

        Args:
            hooks: List of hook metadata to check

        Returns:
            Dictionary mapping hook names to eligibility results
        """
        results = {}
        for hook in hooks:
            results[hook.name] = self.check(hook)
        return results

    def get_eligible_hooks(self, hooks: List[HookMetadata]) -> List[HookMetadata]:
        """
        Filter hooks to only include eligible ones.

        Args:
            hooks: List of hook metadata to filter

        Returns:
            List of eligible hook metadata
        """
        eligible = []
        for hook in hooks:
            result = self.check(hook)
            if result.eligible:
                eligible.append(hook)
        return eligible
