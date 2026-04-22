"""
purpose: "Fixture: module-scoped exception suppresses a c25 local import."
governance_exceptions:
  - {c25: "local import: import json"}
"""
import os


def do_stuff(*args, **kwargs):
    import json
    return json.dumps({"ok": True}, *args, **kwargs)
