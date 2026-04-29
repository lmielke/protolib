"""
script_path: src/protolib/test/core/helpers/gov/c29.py
purpose: "[TO_DELETE] c29 — hardcoded-path check. Flags absolute paths embedded in code."
description: "Hardcoded paths break portability. Use settings, os.path or pathlib anchors."
update_rules: "Do not modify in clones."
"""
import re


def _c29_hardcoded_paths(lines, rel, *args, **kwargs):
    """purpose: Flag literals beginning with drive letters, /home/ or /tmp/."""
    warn, err = [], []
    for i, line in enumerate(lines):
        if line.strip().startswith('#'): continue
        if re.search(r'["\'][A-Z]:\\|["\']/home/|["\']/tmp/', line):
            warn.append(f"line {i+1}: hardcoded path — use settings or os.path")
    return warn, err
