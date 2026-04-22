"""
purpose: "Fixture: exception lives inside the def's docstring, not module-level."
"""
import os


def do_stuff(*args, **kwargs):
    """
    purpose: "Local json import kept deliberate for lazy load."
    governance_exceptions:
      - {c25: "local import: import json"}
    """
    import json
    return json.dumps({"ok": True}, *args, **kwargs)
