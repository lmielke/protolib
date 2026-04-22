"""
script_path: src/protolib/app/protopy.py
purpose: Application object for protolib and all cloned packages.
description: |-
  Orchestrates the call
  chain between argument parsing, contract validation, and API dispatch. Clone owners
  override DefaultClass.run() to customise the execution sequence.
governance_exceptions:
  - c25: "local import in _check_governance() — move to module top"
"""
import importlib, sys

import protolib.app.settings as sts
import protolib.core.settings as core_sts
import protolib.app.arguments as arguments
import protolib.app.contracts as contracts


class DefaultClass:
    """
    purpose: Application object — thin orchestrator.
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
        self._check_governance(*args, **kwargs)
        kw = arguments.mk_args().__dict__
        kw = contracts.checks(*args, **kw)
        self._dispatch(*args, **kw)

    def _check_governance(self, *args, **kwargs):
        """
        purpose: Run the governance suite if settings.run_checks is enabled.
        """
        if not getattr(sts, "run_checks", False):
            return
        from protolib.test.core.test_governance import run as check_governance
        _, errors = check_governance()
        if errors:
            sys.stderr.write(f"\n  {len(errors)} governance error(s) found.\n\n")

    def _dispatch(self, *args, api: str = "help", **kwargs):
        if api == "help":
            return
        mod = _import_api(api)
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
    purpose: Entry point for `proto` console script.
    """
    DefaultClass().run(*args, **kwargs)


if __name__ == "__main__":
    main()
