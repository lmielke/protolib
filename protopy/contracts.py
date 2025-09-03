# contracts.py
import protopy.settings as sts
import os, sys
import protopy.arguments as arguments
from colorama import Fore, Style


def checks(*args, **kwargs):
    kwargs = clean_kwargs(*args, **kwargs)
    check_missing_kwargs(*args, **kwargs)
    kwargs.update(check_target_dir(*args, **kwargs))# clone_remove_line
    check_env_vars(*args, **kwargs)
    return kwargs

def check_env_vars(*args, **kwargs):
    """
    Some processes like pm2 run the application without environment variables.
    This function checks if the required environment variables are set.
    If not it adds them by loading the .env file.
    """
    if os.environ.get('pg_alias') is None:
        from dotenv import load_dotenv
        env_file = os.path.join(sts.project_dir, ".env")
        load_dotenv(env_file)


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

def check_target_dir(*args, api:str, tgt_dir:str=None, **kwargs):# clone_remove_line
    """# clone_remove_line
    First tries to resolve absolute path from the given target directory.# clone_remove_line
    Then checks if the target directory exists and is writable.# clone_remove_line
    """# clone_remove_line
    if api != 'clone':# clone_remove_line
        return {}# clone_remove_line
    if tgt_dir is None:# clone_remove_line
        raise ValueError("Target directory must be specified")# clone_remove_line
    tgt_dir = tgt_dir.replace('/', os.sep)# clone_remove_line
    if tgt_dir == '.' or tgt_dir == './':# clone_remove_line
        tgt_dir = os.getcwd()# clone_remove_line
    if tgt_dir == '..' or tgt_dir == '../':# clone_remove_line
        tgt_dir = os.path.dirname(os.getcwd())# clone_remove_line
    elif tgt_dir.startswith('~'):# clone_remove_line
        tgt_dir = os.path.expanduser(tgt_dir)# clone_remove_line
    elif tgt_dir.startswith(f".{os.sep}"):# clone_remove_line
        # relative path from current working directory# clone_remove_line
        tgt_dir = os.path.join(os.getcwd(), tgt_dir[2:])# clone_remove_line
    # we convert path to absolute path# clone_remove_line
    tgt_dir = os.path.abspath(tgt_dir)# clone_remove_line
    # now we check if the target directory exists# clone_remove_line
    if not os.path.exists(tgt_dir):# clone_remove_line
        raise FileNotFoundError(f"Target directory '{tgt_dir}' does not exist")# clone_remove_line
    if sts.project_dir in tgt_dir:# clone_remove_line
        raise ValueError(f"Target directory '{tgt_dir}' is inside the project directory '{sts.project_dir}'")# clone_remove_line
    return {'tgt_dir': tgt_dir}# clone_remove_line