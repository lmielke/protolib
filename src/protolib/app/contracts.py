"""
script_path: src/protolib/app/contracts.py
purpose: Argument validation and enrichment pipeline for all protolib APIs.
description: |-
  Cleans
  incoming kwargs, checks required parameters against declared contracts, and
  enriches the call with package metadata before dispatch to the target API.
  Failures produce structured error messages with actionable hints.
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""
import os, sys
import protolib.app.settings as sts
from colorama import Fore, Style

_CLONE_REQUIRED = {
    'new_pr_name': 'myhammerlib',
    'new_pg_name': 'myhammer',
    'new_alias': 'myham',
    'tgt_dir': 'C:/temp',
}

def checks(*args, **kwargs):
    cleaned = clean_kwargs(*args, **kwargs)
    check_missing_kwargs(*args, **cleaned)
    cleaned.update(get_package_data(*args, **cleaned))
    cleaned.update(clean_paths(*args, **cleaned))
    check_env_vars(*args, **cleaned)
    return cleaned

def check_env_vars(*args, **kwargs):
    """
    purpose: 'Stub: override in clones to load env vars as needed.'
    """
    pass

def clean_kwargs(*args, **kwargs):
    """
    purpose: Strip whitespace from keys and string values.
    """
    result = {}
    for k, v in kwargs.items():
        result[k.strip()] = v.strip().strip("'") if isinstance(v, str) else v
    return result

def check_missing_kwargs(*args, api: str = "", **kwargs):
    """
    purpose: Check all required kwargs are present for the given API.
    """
    reqs = _CLONE_REQUIRED if api == 'clone' else {}
    missings = {k for k in reqs if k not in kwargs}
    if missings:
        _report_missing(missings, reqs)

def _report_missing(missings: set, reqs: dict, *args, **kwargs):
    sys.stderr.write(f"{Fore.RED}Missing required arguments: {missings}{Style.RESET_ALL}\n")
    sys.stderr.write(f"{Fore.YELLOW}Required: {reqs}{Style.RESET_ALL}\n")
    exit()

def _pkg_data(*args, **kwargs) -> dict:
    return {
        'project_dir': getattr(sts, 'project_dir', None),
        'package_dir': getattr(sts, 'package_dir', None),
        'pr_name': getattr(sts, 'project_name', None),
        'pg_name': getattr(sts, 'package_name', None),
        'is_package': True,
    }

def get_package_data(*args, work_dir: str = None, **kwargs) -> dict:
    """
    purpose: Return package path data derived from settings.py.
    """
    wd = os.path.abspath(work_dir or os.getcwd())
    return {'work_dir': wd, **_pkg_data(*args, **kwargs)}

def clean_paths(*args, **kwargs) -> dict:
    """
    purpose: Normalize all _dir/_path kwargs to canonical absolute paths.
    """
    result = {}
    for n, v in kwargs.items():
        if isinstance(v, str) and ("_dir" in n or "_path" in n):
            result[n] = normalize_path(v, *args, **kwargs)
    return result

def normalize_path(path: str, *args, **kwargs) -> str:
    """
    purpose: Canonicalize user-supplied path to absolute, normalized form.
    """
    if not path:
        return path
    p = os.path.expanduser(path)
    if not os.path.isabs(p):
        p = os.path.abspath(os.path.join(os.getcwd(), p))
    return os.path.normpath(p)
