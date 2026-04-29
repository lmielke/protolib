"""
script_path: src/protolib/test/core/helpers/gov/c8.py
purpose: "[TO_DELETE] c8 — class-presence check. Flags modules without an OOP class definition."
description: "OOP is the primary paradigm; enum-only modules are exempt via __init__ heuristic."
update_rules: "Do not modify in clones."
"""
import re

_C8_ENUM_BASES = r'\((\w+\.)?(Enum|IntEnum|StrEnum|Flag|IntFlag)\)'


def _c8_class_presence(lines, rel, *args, **kwargs):
    """purpose: Flag absence of class defs or classes without __init__ (unless enum)."""
    warn, err = [], []
    classes = [l for l in lines if re.match(r'^class \w+', l)]
    if not classes:
        warn.append("no class definition — verify OOP intent")
        return warn, err
    has_init = any(re.match(r'\s+def (__init__|__post_init__)\(', l) for l in lines)
    all_enum = all(re.search(_C8_ENUM_BASES, c) for c in classes)
    if not has_init and not all_enum:
        warn.append("class(es) without __init__ — may be enum/constant, verify OOP intent")
    return warn, err
