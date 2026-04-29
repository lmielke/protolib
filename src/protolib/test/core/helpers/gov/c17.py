"""
script_path: src/protolib/test/core/helpers/gov/c17.py
purpose: "[TO_DELETE] c17 — module docstring check. Triple-quote docstring with script_path: required."
description: "Validates first-5-non-blank-line docstring; checks closure, script_path, length."
update_rules: "Do not modify in clones."
"""
import re


def _c17_docstring(lines, rel, *args, **kwargs):
    """purpose: Validate module docstring presence, closure, script_path, minimum length."""
    warn, err = [], []
    non_blank = [(i, l.strip()) for i, l in enumerate(lines) if l.strip()][:5]
    if not any(l.startswith('"""') for _, l in non_blank):
        err.append("missing module docstring (triple-quote) in first 5 non-blank lines")
        return warn, err
    text = "".join(lines)
    m = re.search(r'"""(.*?)"""', text, re.DOTALL)
    if not m:
        err.append("module docstring not closed")
        return warn, err
    doc = m.group(1)
    if "script_path:" not in doc:
        err.append("module docstring missing 'script_path:' line")
    desc = re.sub(r'script_path:\s*\S+\n?', '', doc).strip()
    words, sentences = desc.split(), len(re.findall(r'[.!?][\s\n]', desc))
    if len(words) < 25 and sentences < 3:
        warn.append("module docstring too short (add ≥25 words or 3 sentences)")
    return warn, err
