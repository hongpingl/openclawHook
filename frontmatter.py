"""
HOOK.md frontmatter parsing for the OpenClaw Hooks System.
"""

import re
from typing import Any, Dict, Optional, Tuple

import yaml

from .hook_types import HookMetadata


def parse_hook_md(content: str) -> Tuple[Optional[HookMetadata], str]:
    """
    Parse a HOOK.md file and extract metadata from YAML frontmatter.

    Args:
        content: The raw content of the HOOK.md file

    Returns:
        A tuple of (HookMetadata or None, documentation body)
    """
    frontmatter, body = extract_frontmatter(content)
    
    if frontmatter is None:
        return None, body
    
    try:
        metadata_dict = yaml.safe_load(frontmatter)
        if not isinstance(metadata_dict, dict):
            return None, body
    except yaml.YAMLError:
        return None, body

    name = metadata_dict.get("name")
    description = metadata_dict.get("description", "")
    
    if not name:
        return None, body

    metadata = HookMetadata.from_dict(name, description, metadata_dict)
    return metadata, body


def extract_frontmatter(content: str) -> Tuple[Optional[str], str]:
    """
    Extract YAML frontmatter from content.

    Args:
        content: The raw content

    Returns:
        A tuple of (frontmatter string or None, body string)
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        frontmatter = match.group(1)
        body = match.group(2)
        return frontmatter, body
    
    return None, content


def create_hook_md(metadata: HookMetadata, body: str = "") -> str:
    """
    Create a HOOK.md file content from metadata.

    Args:
        metadata: The hook metadata
        body: The documentation body

    Returns:
        The formatted HOOK.md content
    """
    frontmatter_dict: Dict[str, Any] = {
        "name": metadata.name,
        "description": metadata.description,
    }
    
    if metadata.homepage:
        frontmatter_dict["homepage"] = metadata.homepage
    
    openclaw_data: Dict[str, Any] = {}
    
    if metadata.emoji:
        openclaw_data["emoji"] = metadata.emoji
    
    if metadata.events:
        openclaw_data["events"] = metadata.events
    
    if metadata.export != "default":
        openclaw_data["export"] = metadata.export
    
    if metadata.requires:
        requires_data = {}
        if metadata.requires.bins:
            requires_data["bins"] = metadata.requires.bins
        if metadata.requires.any_bins:
            requires_data["anyBins"] = metadata.requires.any_bins
        if metadata.requires.env:
            requires_data["env"] = metadata.requires.env
        if metadata.requires.config:
            requires_data["config"] = metadata.requires.config
        if metadata.requires.os:
            requires_data["os"] = metadata.requires.os
        if requires_data:
            openclaw_data["requires"] = requires_data
    
    if metadata.always:
        openclaw_data["always"] = True
    
    if metadata.install:
        openclaw_data["install"] = metadata.install
    
    if openclaw_data:
        frontmatter_dict["metadata"] = {"openclaw": openclaw_data}
    
    frontmatter = yaml.dump(frontmatter_dict, default_flow_style=False, sort_keys=False)
    
    return f"---\n{frontmatter}---\n\n{body}"


def validate_hook_md(content: str) -> Tuple[bool, list]:
    """
    Validate a HOOK.md file content.

    Args:
        content: The raw content of the HOOK.md file

    Returns:
        A tuple of (is_valid, list of error messages)
    """
    errors = []
    
    metadata, body = parse_hook_md(content)
    
    if metadata is None:
        errors.append("Missing or invalid YAML frontmatter")
        return False, errors
    
    if not metadata.name:
        errors.append("Missing required field: name")
    
    if not metadata.description:
        errors.append("Missing recommended field: description")
    
    if not metadata.events:
        errors.append("Missing recommended field: events in metadata.openclaw")
    
    return len(errors) == 0, errors
