"""
script_path: src/protolib/test/core/helpers/gov/c20.py
purpose: "[TO_DELETE] c20 — name-guard check. Modules with main() must guard on __name__ == '__main__'."
description: "Without the guard the module body runs on import, not only when executed directly."
update_rules: "Do not modify in clones."
"""
import re


def _c20_name_guard(lines, rel, *args, **kwargs):
    """purpose: Flag main() without an accompanying __name__ guard."""
    warn, err = [], []
    if not any(re.match(r'^def main\(', l) for l in lines):
        return warn, err
    if not any(re.match(r'if __name__\s*==\s*[\'"]__main__[\'"]', l) for l in lines):
        warn.append("has main() but no if __name__ == '__main__' guard")
    return warn, err
