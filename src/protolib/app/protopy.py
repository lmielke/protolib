"""
script_path: src/protolib/app/protopy.py
description: >-
  Orchestrates the call chain between argument parsing, contract validation, and API dispatch
  for protolib and cloned packages. Instantiates DefaultClass to execute the run sequence,
  where clone owners override the method to customise behavior. The dispatch mechanism resolves
  API names against configured packages and imports the matching module for execution.
tags:
- cli
- infra
- parsing
"""
import importlib

import protolib.core.settings as core_sts
import protolib.app.arguments as arguments
from protolib.app.contracts import Contracts as _Contracts


class DefaultClass:
    """
    "description": >-
      Contains only instantiations and calls.
          Override run() in clones to customise the execution sequence.
    """

    def __init__(self, *args, pg_name: str = None, verbose: int = 0, **kwargs) -> None:
        self.verbose = verbose
        self.pg_name = pg_name

    def __str__(self, *args, **kwargs) -> str:
        return f"DefaultClass: {self.pg_name = }"

    def run(self, *args, **kwargs):
        kw = arguments.mk_args().__dict__
        self._dispatch(*args, **_Contracts().checks(*args, **kw), **kwargs)

    def _dispatch(self, *args, api: str = "help", **kwargs):
        if api == "help":
            return
        mod = _import_api(api, *args, **kwargs)
        mod.main(*args, **kwargs)

def _import_api(name: str, *args, **kwargs):
    for _, pkg in core_sts.api_packages:
        try:
            return importlib.import_module(f"{pkg}.{name}")
        except ModuleNotFoundError:
            continue
    raise ModuleNotFoundError(f"API '{name}' not found in {core_sts.api_packages}")

def main(*args, **kwargs):
    """
    description: Entry point for `proto` console script.
    """
    DefaultClass(*args, **kwargs).run(*args, **kwargs)


if __name__ == "__main__":
    main()
