# contracts.py
import protolib.settings as sts
import os, sys
import protolib.arguments as arguments
from colorama import Fore, Style


def checks(*args, **kwargs):
    kwargs = clean_kwargs(*args, **kwargs)
    check_missing_kwargs(*args, **kwargs)
    kwargs.update(get_package_data(*args, **kwargs))
    kwargs.update(clean_paths(*args, **kwargs))
    check_env_vars(*args, **kwargs)
    return kwargs

def check_env_vars(*args, **kwargs):
    """
    Stub: override in your package's contracts.py to load env vars as needed.
    Protolib-specific dotenv/pg_alias logic has been removed from the template.
    """
    pass

def clean_kwargs(*args, **kwargs):
    # kwargs might come from a LLM api and might be poluted with whitespaces ect.
    cleaned_kwargs = {}
    for k, vs in kwargs.items():
        if isinstance(vs, str):
            cleaned_kwargs[k.strip()] = vs.strip().strip("'")
        else:
            cleaned_kwargs[k.strip()] = vs
    return cleaned_kwargs

def check_missing_kwargs(*args, api,  **kwargs):
    """
    Uses arguments to check if all required kwargs are provided
    """
    missings = set()
    requireds = {}
    if api == 'clone':                                      # clone_remove_line
        requireds = {                                       # clone_remove_line
                        'new_pr_name': 'myhammerlib',       # clone_remove_line
                        'new_pg_name': 'myhammer',          # clone_remove_line
                        'new_alias': 'myham',               # clone_remove_line
                        'tgt_dir': 'C:/temp',               # clone_remove_line
                        }                                   # clone_remove_line
    for k, v in requireds.items():
        if k not in kwargs.keys():
            missings.add(k)
    if missings:
        print(f"{Fore.RED}Missing required arguments: {missings}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Required arguments are: {requireds}{Style.RESET_ALL}")
        exit()

def get_package_data(*args, work_dir:str=None, **kwargs) -> dict:
    """
    Returns package path data derived from settings.py.
    Stub: clones derive their own paths from their settings module — no tree traversal needed.
    """
    work_dir = os.path.abspath(work_dir if work_dir is not None else os.getcwd())
    return {
        'work_dir': work_dir,
        'project_dir': getattr(sts, 'project_dir', None),
        'package_dir': getattr(sts, 'package_dir', None),
        'pr_name': getattr(sts, 'project_name', None),
        'pg_name': getattr(sts, 'package_name', None),
        'is_package': True,
    }

def clean_paths(*args, **kwargs) -> dict:
    """
    WHY: Normalize *_dir/*_path and resolve missing files if path doesn't exist.
    """
    normalizeds = {}
    for n, v in kwargs.items():
        if isinstance(v, str) and any(t in n for t in {"_dir", "_path"}):
            normalizeds[n] = normalize_path(v, *args, **kwargs)
    return normalizeds

def normalize_path(path: str, *args, **kwargs) -> str:
    """
    WHY: Canonicalize user-supplied paths consistently across OS.
    """
    if not path:
        return path
    p = os.path.expanduser(path)
    if not os.path.isabs(p):
        p = os.path.abspath(os.path.join(os.getcwd(), p))
    return os.path.normpath(p)