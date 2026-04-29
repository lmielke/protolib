"""
script_path: src/protolib/test/core/gov/helpers/c41.py
paths: ["**/*.py"]
purpose: "Helper: c41 — duplicate basenames across the source tree (error)."
description: |-
  Cross-file scan. Builds a basename → [rel, ...] map once per process
  via base.discover_sources, cached. When the current file shares its
  basename with another source, emits one error record listing all
  collisions.
update_rules: "Do not modify in clones. No thresholds."
"""
import os

from protolib.test.core.gov.base import discover_sources

_BASENAME_MAP: dict | None = None


def run(*args, rel, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    others = _basename_map().get(os.path.basename(rel), [])
    if len(others) <= 1: return []
    return [{"level": "error", "line": 1, "scope": "module",
             "technical_message": f"duplicate basename at {', '.join(others)}"}]


def _basename_map(*args, **kwargs) -> dict:
    """purpose: 'Lazy basename → [rel, ...] map across all source files.'"""
    global _BASENAME_MAP
    if _BASENAME_MAP is not None: return _BASENAME_MAP
    m = {}
    for r in discover_sources(): m.setdefault(os.path.basename(r), []).append(r)
    _BASENAME_MAP = m
    return _BASENAME_MAP
