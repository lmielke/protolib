"""
script_path: src/protolib/test/data/governance_fixtures/wrong_scope_exception.py
purpose: "Fixture: def-scope exception targets a record whose scope is module."
"""
import os


def do_stuff(*args, **kwargs):
    """
    purpose: "Def hosts an exception for c25 but c25 records at module scope."
    governance_exceptions:
      - {c25: "local import: import json"}
    """
    import json
    return json.dumps({"ok": True}, *args, **kwargs)
