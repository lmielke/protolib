# contracts.py
import protopy.settings as sts
import os, sys
import protopy.arguments as arguments


def checks(*args, **kwargs):
    kwargs = clean_kwargs(*args, **kwargs)
    check_missing_kwargs(*args, **kwargs)
    kwargs.update(check_target_dir(*args, **kwargs))
    return kwargs


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
    if api == 'clone':
        requireds = {
                        'new_pr_name': 'myhammerlib',
                        'new_pg_name': 'myhammer',
                        'new_alias': 'myham',
                        'tgt_dir': 'C:/temp',
                        }
    else:
        requireds = {}
    missings = set()
    for k, v in requireds.items():
        if k not in kwargs.keys():
            missings.add(k)
    if missings:
        print(f"{sts.RED}Missing required arguments: {missings}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Required arguments are: {requireds}{Style.RESET_ALL}")
        exit()

def check_target_dir(*args, api:str, tgt_dir:str=None, **kwargs):
    """
    First tries to resolve absolute path from the given target directory.
    Then checks if the target directory exists and is writable.
    """
    if api != 'clone':
        return {}
    if tgt_dir is None:
        raise ValueError("Target directory must be specified")
    tgt_dir = tgt_dir.replace('/', os.sep)
    if tgt_dir == '.':
        tgt_dir = os.getcwd()
    elif tgt_dir.startswith('~'):
        tgt_dir = os.path.expanduser(tgt_dir)
    elif tgt_dir.startswith(f".{os.sep}"):
        # relative path from current working directory
        tgt_dir = os.path.join(os.getcwd(), tgt_dir[2:])
    # we convert path to absolute path
    tgt_dir = os.path.abspath(tgt_dir)
    # now we check if the target directory exists
    if not os.path.exists(tgt_dir):
        raise FileNotFoundError(f"Target directory '{tgt_dir}' does not exist")
    if sts.project_dir in tgt_dir:
        raise ValueError(f"Target directory '{tgt_dir}' is inside the project directory '{sts.project_dir}'")
    return {'tgt_dir': tgt_dir}