"""
script_path: src/protolib/core/admin_args.py
description: >-
  Defines the argument parser for the proto-admin CLI entry point, supporting clone and sync
  subcommands. It specifies flags for project naming, target directories, and installation
  options. This module isolates framework-level operations from application-level API dispatch
  to maintain consistency across cloned packages.
tags:
- cli
- infra
- settings
governance_exceptions:
- c8: no class definition — verify OOP intent
"""
import argparse


_SUBCOMMANDS = ("clone", "sync")

def mk_args(*args, **kwargs):
    """
    purpose: Parse admin CLI arguments.
    description: Returns argparse.Namespace.
    """
    parser = argparse.ArgumentParser(prog="proto-admin",
        description="protolib framework admin: clone, sync.")
    sub = parser.add_subparsers(dest="command", required=True)
    _add_clone(sub, *args, **kwargs)
    _add_sync(sub, *args, **kwargs)
    return parser.parse_args()

_CLONE_SPECS = [
    (("-pr", "--new_pr_name"), {"type": str, "help": "project name (top folder)"}),
    (("-n",  "--new_pg_name"), {"type": str, "help": "package name inside project"}),
    (("-a",  "--new_alias"),   {"type": str, "help": "package alias"}),
    (("-t",  "--tgt_dir"),     {"type": str, "help": "target directory for clone"}),
    (("-p",  "--py_version"),  {"type": str, "help": "python version"}),
    (("--port",),              {"type": str, "help": "port for server.py"}),
    (("--install",),           {"action": "store_true", "help": "run uv sync after clone"}),
    (("-y",  "--yes"),         {"action": "store_true", "help": "skip prompts"}),
    (("-v",  "--verbose"),     {"type": int, "default": 0, "help": "0:silent,1:user,2:debug"}),
]

def _add_clone(sub, *args, **kwargs):
    p = sub.add_parser("clone", help="Clone the package template into a new project.")
    for flags, kw in _CLONE_SPECS: p.add_argument(*flags, **kw)

def _add_sync(sub, *args, **kwargs):
    p = sub.add_parser("sync", help="Push core/ + helpers/ to all registered clones.")
    p.add_argument("-v", "--verbose", type=int, default=0)
