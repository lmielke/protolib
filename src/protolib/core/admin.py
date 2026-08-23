"""
script_path: src/protolib/core/admin.py
description: >-
  Dispatches proto-admin subcommands to the correct core creator module, routing clone and
  sync operations. Maintains strict separation from the application-level proto entry point
  to ensure framework operations remain available in customized clones. Consumed by the proto-admin
  console script entry point.
tags:
- cli
- infra
"""
import sys

from protolib.core import admin_args
from protolib.core.creator.clone import main as clone_main
from protolib.core.creator.sync import main as sync_main


class AdminDispatcher:
    """
    description: Routes admin subcommands to their implementation modules.
    """

    def __init__(self, *args, **kwargs):
        pass

    def dispatch(self, *args, **kwargs):
        handler = self._handler(*args, **kwargs)
        handler(*args, **kwargs)

    def _handler(self, *args, command: str, **kwargs):
        mapping = {"clone": self._clone, "sync": self._sync}
        if command not in mapping:
            sys.stderr.write(f"Unknown admin command: {command}\n")
            sys.exit(2)
        return mapping[command]

    @staticmethod
    def _clone(*args, **kwargs):
        clone_main(*args, **kwargs)

    @staticmethod
    def _sync(*args, **kwargs):
        sync_main(*args, **kwargs)

def main(*args, **kwargs):
    """
    description: Entry point for `proto-admin` console script.
    """
    ns = admin_args.mk_args(*args, **kwargs)
    AdminDispatcher().dispatch(**vars(ns))


if __name__ == "__main__":
    main()
