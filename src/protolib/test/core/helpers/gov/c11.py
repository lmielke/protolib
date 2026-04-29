"""
script_path: src/protolib/test/core/helpers/gov/c11.py
purpose: "[TO_DELETE] c11 — line length check. Mandatory-fix: max 95 characters per code line."
description: "Comment-only lines are exempt; wrap or extract locals to stay under the limit."
update_rules: "Do not modify in clones."
"""


def _c11_line_length(lines, rel, *args, **kwargs):
    """purpose: Flag non-comment lines exceeding 95 characters."""
    warn, err = [], []
    for i, line in enumerate(lines):
        s = line.rstrip("\n")
        if s.strip() and not s.strip().startswith("#") and len(s) > 95:
            warn.append(f"line {i+1}: {len(s)} chars (max 95)")
    return warn, err
