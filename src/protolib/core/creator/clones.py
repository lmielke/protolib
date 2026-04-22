"""
script_path: src/protolib/core/creator/clones.py
purpose: Persist and load clone locations for sync propagation.
description: |-
  Writes clone paths to ~/.protolib/clones.yml on every clone, and reads
  them back so sync can propagate framework updates to all registered clones.
"""
import tomllib, yaml
from datetime import datetime
from pathlib import Path

import protolib.core.settings as sts


class Clones:
    """
    purpose: Manages clones file at ~/.protolib/clones.yml.
    """

    def __init__(self, *args, path: Path = None, **kwargs):
        """purpose: Initialize clones file with optional path override."""
        self.path = path or Path(sts.resources_dir) / "clones.yml"

    def add(self, project_path: str, *args, **kwargs) -> None:
        """purpose: Add or update clone entry. Deduplicates by resolved path."""
        path = Path(project_path).resolve()
        entries = [e for e in self.load() if Path(e["path"]).resolve() != path]
        entries.append({"path": str(path), "name": _pkg_name(path),
                        "cloned_at": datetime.now().isoformat(timespec="seconds")})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.dump({"clones": entries}, default_flow_style=False))

    def remove(self, project_path: str, *args, **kwargs) -> None:
        """purpose: Remove entry matching project_path. No-op if absent."""
        target = Path(project_path).resolve()
        entries = [e for e in self.load() if Path(e["path"]).resolve() != target]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(yaml.dump({"clones": entries}, default_flow_style=False))

    def load(self, *args, **kwargs) -> list:
        """purpose: Return list of clone entries, or [] if file missing."""
        if not self.path.exists():
            return []
        return (yaml.safe_load(self.path.read_text()) or {}).get("clones", [])

def _pkg_name(project_path: Path, *args, **kwargs) -> str:
    """purpose: Read package name from project_path/pyproject.toml."""
    data = tomllib.loads((project_path / "pyproject.toml").read_text())
    return data.get("project", {}).get("name", project_path.name)
