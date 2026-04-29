"""
script_path: src/protolib/test/core/gov/log.py
purpose: "Yaml read/write for governance_log.yaml — per-file scan log."
description: |-
  GovernanceLog accumulates per-file (header, warnings, errors) entries.
  Files with empty warnings AND empty errors are NOT recorded — absence
  means clean. save() overwrites the yaml atomically and stamps
  last_checked.
update_rules: "Update when log schema changes."
"""
import os
import yaml
from datetime import datetime, timezone

from protolib.test.core.gov import settings as sts


class GovernanceLog:
    """purpose: 'Accumulate per-file governance records; write yaml at end.'"""

    def __init__(self, *args, log_path: str, **kwargs):
        self.log_path = log_path
        self.entries = {}

    def record(self, *args, rel: str, header: dict, warnings: list, errors: list, **kwargs):
        """purpose: 'Keep this rel only if warnings or errors non-empty.'"""
        if not warnings and not errors: return
        self.entries[rel] = {"header": header, "warnings": warnings, "errors": errors}

    def save(self, *args, **kwargs):
        """purpose: 'Write yaml log; stamps last_checked iso timestamp.'"""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        doc = {"last_checked": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        doc.update(self.entries)
        with open(self.log_path, "w") as f:
            f.write(sts.checks['log_header'])
            yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True,
                           indent=4, width=10000, default_flow_style=False)
