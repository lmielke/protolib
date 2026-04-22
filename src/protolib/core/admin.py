"""
script_path: src/protolib/core/admin.py
purpose: Admin CLI entry point for the protolib framework.
description: |-
  Dispatches `proto-admin
  <command>` to the correct core creator module (clone or sync). Kept strictly
  separate from the application-level `proto` entry point (app/protopy.py) so
  that framework operations remain available even in heavily customised clones.
"""
import sys

from protolib.core import arguments as admin_args
from protolib.core.creator.clone import main as clone_main
from protolib.core.creator.sync import main as sync_main


class AdminDispatcher:
    """
    purpose: Routes admin subcommands to their implementation modules.
    """

    def __init__(self, *args, **kwargs):
        pass

    def dispatch(self, *args, command: str, **kwargs):
        handler = self._handler(command=command)
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
    purpose: Entry point for `proto-admin` console script.
    """
    ns = admin_args.mk_args()
    AdminDispatcher().dispatch(**vars(ns))


if __name__ == "__main__":
    main()
