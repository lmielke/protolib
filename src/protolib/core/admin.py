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
        """description: 'Stateless dispatcher; no instance state required.'"""
        pass

    def dispatch(self, *args, **kwargs):
        """description: 'Resolve and call the handler for the given command.'"""
        handler = self._handler(*args, **kwargs)
        handler(*args, **kwargs)

    def _handler(self, *args, command: str, **kwargs):
        """description: 'Return the bound method for command; exit 2 if unknown.'"""
        mapping = {"clone": self._clone, "sync": self._sync}
        if command not in mapping:
            sys.stderr.write(f"Unknown admin command: {command}\n")
            sys.exit(2)
        return mapping[command]

    @staticmethod
    def _clone(*args, **kwargs):
        """description: 'Delegate to clone_main.'"""
        clone_main(*args, **kwargs)

    @staticmethod
    def _sync(*args, **kwargs):
        """description: 'Delegate to sync_main.'"""
        sync_main(*args, **kwargs)

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "AdminDispatcher(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Short text identifying this dispatcher.'"""
        return "AdminDispatcher"

def main(*args, **kwargs):
    """
    description: Entry point for `proto-admin` console script.
    """
    ns = admin_args.mk_args(*args, **kwargs)
    AdminDispatcher().dispatch(**vars(ns))


if __name__ == "__main__":
    main()
