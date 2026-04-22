"""
purpose: "Fixture: docstring has no exception block; violation remains unfiltered."
"""
import os


def do_stuff(*args, **kwargs):
    import json
    return json.dumps({"ok": True}, *args, **kwargs)
