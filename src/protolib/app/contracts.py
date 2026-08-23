"""
script_path: src/protolib/app/contracts.py
description: >-
  Validates and enriches incoming keyword arguments for protolib API calls before dispatch.
  Strips whitespace, checks required parameters against declared contracts, and normalizes
  path values to absolute forms. Injects package metadata from settings and reports missing
  arguments with structured error messages. Consumed by all protolib API entry points as a
  pre-dispatch pipeline.
tags:
- infra
- parsing
- rule
"""
import os, sys
import protolib.app.settings as sts
from colorama import Fore, Style


class Contracts:
    """
    purpose: "Pre-dispatch kwarg validator and enricher for protolib APIs."
    description: >-
      Owns the required-argument registry and the full validation pipeline.
      Cleans kwarg strings, enforces per-API required fields, injects package
      metadata, and normalises path values. Override check_env_vars in clones
      to add environment-variable injection.
    """

    def __init__(self, *args, **kwargs):
        """description: 'No per-instance state; logic is driven by kwargs at call time.'"""

    _CLONE_REQUIRED = {
        'new_pr_name': 'myhammerlib',
        'new_pg_name': 'myhammer',
        'new_alias': 'myham',
        'tgt_dir': 'C:/temp',
    }

    def checks(self, *args, **kwargs) -> dict:
        """
        description: Full pipeline — clean, validate, and enrich kwargs.
        """
        cleaned = self.clean_kwargs(*args, **kwargs)
        self.check_missing_kwargs(*args, **kwargs)
        cleaned.update(self.get_package_data(*args, **kwargs))
        cleaned.update(self.clean_paths(*args, **kwargs))
        self.check_env_vars(*args, **kwargs)
        return cleaned

    def check_env_vars(self, *args, **kwargs):
        """
        description: 'Stub: override in clones to load env vars as needed.'
        """
        pass

    def clean_kwargs(self, *args, **kwargs) -> dict:
        """
        description: Strip whitespace from keys and string values.
        """
        result = {}
        for k, v in kwargs.items():
            result[k.strip()] = v.strip().strip("'") if isinstance(v, str) else v
        return result

    def check_missing_kwargs(self, *args, api: str = "", **kwargs):
        """
        description: Check all required kwargs are present for the given API.
        """
        reqs = self._CLONE_REQUIRED if api == 'clone' else {}
        missings = {k for k in reqs if k not in kwargs}
        if missings:
            self._report_missing(missings, reqs, *args, **kwargs)

    def get_package_data(self, *args, work_dir: str = None, **kwargs) -> dict:
        """
        description: Return package path data derived from settings.py.
        """
        wd = os.path.abspath(work_dir or os.getcwd())
        return {'work_dir': wd, **self._pkg_data(*args, **kwargs)}

    def clean_paths(self, *args, **kwargs) -> dict:
        """
        description: Normalize all _dir/_path kwargs to canonical absolute paths.
        """
        result = {}
        for n, v in kwargs.items():
            if isinstance(v, str) and ("_dir" in n or "_path" in n):
                result[n] = self.normalize_path(v, *args, **kwargs)
        return result

    def normalize_path(self, path: str, *args, **kwargs) -> str:
        """
        description: Canonicalize user-supplied path to absolute, normalized form.
        """
        if not path:
            return path
        p = os.path.expanduser(path)
        if not os.path.isabs(p):
            p = os.path.abspath(os.path.join(os.getcwd(), p))
        return os.path.normpath(p)

    def _pkg_data(self, *args, **kwargs) -> dict:
        return {
            'project_dir': getattr(sts, 'project_dir', None),
            'package_dir': getattr(sts, 'package_dir', None),
            'pr_name': getattr(sts, 'project_name', None),
            'pg_name': getattr(sts, 'package_name', None),
            'is_package': True,
        }

    def _report_missing(self, missings: set, reqs: dict, *args, **kwargs):
        sys.stderr.write(f"{Fore.RED}Missing required arguments: {missings}{Style.RESET_ALL}\n")
        sys.stderr.write(f"{Fore.YELLOW}Required: {reqs}{Style.RESET_ALL}\n")
        exit()
