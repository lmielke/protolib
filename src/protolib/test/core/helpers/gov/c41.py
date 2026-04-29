"""
script_path: src/protolib/test/core/helpers/gov/c41.py
purpose: "[TO_DELETE] c41 — filename-collision check. Flags .py basenames appearing at >1 source location."
description: "Ambiguous imports and grep noise result from duplicate basenames across subpackages."
update_rules: "Do not modify in clones."
"""
import os
from protolib.test.core.helpers.gov.base import discover_sources

_BASENAME_MAP = None


def _basename_map(*args, **kwargs) -> dict:
    """purpose: Lazy basename → [rel, ...] map across all source files."""
    global _BASENAME_MAP
    if _BASENAME_MAP is None:
        m = {}
        for rel in discover_sources():
            m.setdefault(os.path.basename(rel), []).append(rel)
        _BASENAME_MAP = m
    return _BASENAME_MAP


def _c41_filename_collision(lines, rel, *args, **kwargs):
    """purpose: Flag .py basenames that appear at more than one source location."""
    others = _basename_map().get(os.path.basename(rel), [])
    if len(others) <= 1: return [], []
    return [], [f"duplicate basename at {', '.join(others)}"]
