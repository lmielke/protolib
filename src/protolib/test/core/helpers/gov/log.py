"""
script_path: src/protolib/test/core/helpers/gov/log.py
purpose: "[TO_DELETE] Stateful I/O for governance scan log and exceptions log."
description: |-
  GovernanceLog owns the mtime-based incremental scan cache at LOG_PATH.
  _save_exceptions_log dumps per-file exception rows grouped by rule code.
  Isolated here so gov/base.py stays pure.
update_rules: "Do not modify in clones."
"""
import os, yaml
from datetime import datetime as dt
import protolib.core.settings as sts
from protolib.test.core.helpers.gov.meta import _docstring_nodes, _docstring_excs_safe

LOG_PATH = os.path.join(sts.test_dir, "governance_log.yaml")
EXCS_LOG_PATH = os.path.join(sts.test_dir, "governance_exceptions_log.yaml")


class GovernanceLog:
    """
    purpose: "Read and write the mtime-based incremental scan log."
    description: "Keyed by rel path; stale() drives re-scan; prune() drops dead keys."
    """

    MTIME = int(os.path.getmtime(__file__))

    def __init__(self, *args, **kwargs):
        self.data = {}
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH) as f:
                self.data = yaml.safe_load(f) or {}

    def stale(self, *args, key: str, mtime: float, **kwargs) -> bool:
        """purpose: True when file mtime or linter mtime diverges from cached entry."""
        entry = self.data.get(key, {})
        return int(entry.get("mtime", 0)) != int(mtime) or \
               int(entry.get("linter_mtime", 0)) != self.MTIME

    def record(self, *args, key: str, mtime: float, status: str,
               warnings: list, errors: list, **kwargs):
        """purpose: Store a scan result for `key`."""
        self.data[key] = {
            "mtime": mtime, "linter_mtime": self.MTIME,
            "last_checked": dt.now().isoformat(timespec="seconds"),
            "status": status, "warnings": warnings, "errors": errors,
        }

    def prune(self, *args, active_keys: set, **kwargs):
        """purpose: Remove log entries for files no longer in discover_sources."""
        self.data = {k: v for k, v in self.data.items() if k in active_keys}

    def save(self, *args, **kwargs):
        """purpose: Serialize data to LOG_PATH as blank-line-separated YAML chunks."""
        chunks = [
            yaml.dump({k: v}, default_flow_style=False, sort_keys=False, indent=4).rstrip()
            for k, v in self.data.items()
        ]
        with open(LOG_PATH, "w") as f:
            f.write("\n\n".join(chunks) + "\n")


def _collect_file_exceptions(tree, rel, file_records, *args, **kwargs) -> list:
    """purpose: All governance_exceptions entries in tree, with match count from records."""
    if tree is None: return []
    out = []
    for node, scope, line in _docstring_nodes(tree):
        for e in _docstring_excs_safe(node):
            out += _build_exc_row(e, node, scope, line, rel, file_records)
    return out


def _build_exc_row(e, node, scope, line, rel, file_records, *args, **kwargs) -> list:
    """purpose: Build one exception row from (entry, node, scope, line, rel)."""
    if not isinstance(e, dict) or len(e) != 1: return []
    (ec, et), = e.items()
    name = getattr(node, 'name', None) or os.path.basename(rel)
    hits = sum(1 for r in file_records.get(ec, [])
               if r['technical_message'] == et and r['scope'] == scope)
    return [{'file': rel, 'code': ec, 'scope': scope, 'line': line,
             'node': name, 'tech': et, 'matches': hits}]


def _save_exceptions_log(rows, path, *args, **kwargs):
    """purpose: Dump exceptions grouped by rule code to YAML."""
    data = {'generated_at': dt.now().isoformat(timespec='seconds'),
            'total': len(rows), 'by_rule': _group_exceptions(rows)}
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False,
                  indent=2, allow_unicode=True)


def _group_exceptions(rows, *args, **kwargs) -> dict:
    """purpose: Bucket exception rows by code; drop the 'code' key from each row."""
    by_rule = {}
    for r in rows:
        by_rule.setdefault(r['code'], []).append(
            {k: r[k] for k in ('file', 'scope', 'line', 'node', 'tech', 'matches')})
    return by_rule
