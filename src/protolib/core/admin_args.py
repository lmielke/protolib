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
"""
import argparse


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


class AdminArgs:
    """
    description: "Owns the ArgumentParser for clone and sync subcommands."
    """

    def __init__(self, *args, **kwargs):
        """description: 'Build parser and attach clone/sync subparsers.'"""
        self.parser = argparse.ArgumentParser(
            prog="proto-admin", description="protolib framework admin: clone, sync.")
        sub = self.parser.add_subparsers(dest="command", required=True)
        self._add_clone(sub, *args, **kwargs)
        self._add_sync(sub, *args, **kwargs)

    def __repr__(self, *args, **kwargs):
        """description: 'Machine-readable identity.'"""
        return "AdminArgs()"

    def __str__(self, *args, **kwargs):
        """description: 'Human-readable identity.'"""
        return "AdminArgs(proto-admin)"

    def parse(self, *args, **kwargs):
        """description: 'Return parsed argparse.Namespace.'"""
        return self.parser.parse_args()

    def _add_clone(self, sub, *args, **kwargs):
        """description: 'Attach clone subparser with full flag set.'"""
        p = sub.add_parser("clone", help="Clone the package template into a new project.")
        for flags, kw in _CLONE_SPECS: p.add_argument(*flags, **kw)

    def _add_sync(self, sub, *args, **kwargs):
        """description: 'Attach sync subparser with verbosity flag.'"""
        p = sub.add_parser("sync", help="Push core/ + helpers/ to all registered clones.")
        p.add_argument("-v", "--verbose", type=int, default=0)

def mk_args(*args, **kwargs):
    """description: 'Module-level shim — delegates to AdminArgs().parse().'"""
    return AdminArgs(*args, **kwargs).parse(*args, **kwargs)
