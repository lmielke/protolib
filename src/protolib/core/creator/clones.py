"""
script_path: src/protolib/core/creator/clones.py
description: >-
  Manages the clone registry at ~/.protolib/clones.yml by persisting and loading project paths
  for sync propagation. Deduplicates entries by resolved path and extracts package names from
  pyproject.toml. Consumed by the sync subsystem to identify all registered clones for framework
  updates.
tags:
- infra
- settings
- staging
"""
import tomllib, yaml
from datetime import datetime
from pathlib import Path

import protolib.core.settings as sts


class Clones:
    """
    description: Manages clones file at ~/.protolib/clones.yml.
    """

    def __init__(self, *args, path: Path = None, **kwargs):
        """description: Initialize clones file with optional path override."""
        self.path = path or Path(sts.resources_dir) / "clones.yml"

    def add(self, project_path: str, *args, **kwargs) -> None:
        """description: Add or update clone entry. Deduplicates by resolved path."""
        path = Path(project_path).resolve()
        entries = [e for e in self.load(*args, **kwargs) if Path(e["path"]).resolve() != path]
        entries.append({"path": str(path), "name": _pkg_name(path, *args, **kwargs),
                        "cloned_at": datetime.now().isoformat(timespec="seconds")})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.dump({"clones": entries}, default_flow_style=False))

    def remove(self, project_path: str, *args, **kwargs) -> None:
        """description: Remove entry matching project_path. No-op if absent."""
        target = Path(project_path).resolve()
        entries = [e for e in self.load(*args, **kwargs) if Path(e["path"]).resolve() != target]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.dump({"clones": entries}, default_flow_style=False))

    def load(self, *args, **kwargs) -> list:
        """description: Return list of clone entries, or [] if file missing."""
        if not self.path.exists():
            return []
        return (yaml.safe_load(self.path.read_text()) or {}).get("clones", [])

def _pkg_name(project_path: Path, *args, **kwargs) -> str:
    """description: Read package name from project_path/pyproject.toml."""
    data = tomllib.loads((project_path / "pyproject.toml").read_text())
    return data.get("project", {}).get("name", project_path.name)
