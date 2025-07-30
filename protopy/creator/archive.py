# archive.py
# from . import arguments
import os, re, sys, yaml
from tabulate import tabulate
from datetime import datetime as dt 
import colorama as color
color.init()
import shutil
import protopy.settings as sts

def collect_ignored_dirs(source, ignore_dirs, *args, **kwargs):
    """
    Uses os.walk and regular expressions to collect directories to be ignored.

    Args:
        source (str): The root directory to start searching from.
        ignore_dirs (list of str): Regular expressions for directory paths to ignore.

    Returns:
        set: A set of directories to be ignored.
    """
    ignored = set()
    regexs = [re.compile(d) for d in ignore_dirs]

    for root, dirs, _ in os.walk(source, topdown=True):
        for dir in dirs:
            dir_path = os.path.join(root, dir).replace(os.sep, '/')
            if any(regex.search(dir_path) for regex in regexs):
                ignored.add(os.path.normpath(dir_path))
    return ignored

def custom_ignore(ignored):
    """
    Custom ignore function for shutil.copytree.

    Args:
        ignored (set): Set of directory paths to ignore.

    Returns:
        callable: A function that shutil.copytree can use to determine what to ignore.
    """
    def _ignore_func(dir, cs):
        return set(c for c in cs if os.path.join(dir, c) in ignored)
    return _ignore_func

def archive(srctgtPaths, ignore_dirs=None, *args, **kwargs):
    """
    Archives files and directories, excluding directories that match patterns in ignore_dirs.

    Args:
        srctgtPaths (list of tuples): List containing source and target paths.
        ignore_dirs (list of str): Regular expressions for directory paths to ignore.

    Returns:
        List of tuples: The source and target paths used for archiving.
    """
    # run archiving
    errors, dir_count = [], 0
    archiveds = tabulate(srctgtPaths,
                    headers=['source', 'target'], tablefmt='psql', showindex=True).split('\n')
    print((
            f'{color.Fore.YELLOW}Now Archiving to: {color.Style.RESET_ALL}'
            f'{os.path.dirname(srctgtPaths[0][-1])} ...'
            f'\n{archiveds[0]}'
            f'\n{archiveds[1]}'
            f'\n{archiveds[2]}'
            )
    )
    for i, (source, target) in enumerate(srctgtPaths):
        try:
            ignored = collect_ignored_dirs(source, ignore_dirs)
            if os.path.isdir(source):
                os.makedirs(target, exist_ok=True)
                for root, dirs, files in os.walk(source, topdown=True):
                    dirs[:] = [d for d in dirs if not os.path.normpath(os.path.join(root, d)) in ignored]
                    for file in files:
                        src_path = os.path.normpath(os.path.join(root, file))
                        if not src_path in ignored:
                            relative_path = os.path.relpath(src_path, source)
                            dest_path = os.path.join(target, relative_path)
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            shutil.copy2(src_path, dest_path)
                            dir_count += 1
            elif os.path.isfile(source):
                shutil.copyfile(source, target)
            print(f"{color.Fore.WHITE}{archiveds[i+3]}{color.Style.RESET_ALL}")
        except Exception as e:
            print(f"{color.Fore.RED}{archiveds[i+3]} -> {e}{color.Style.RESET_ALL}")
            errors.append((source, target, e))
    if not errors:
        print(f"{archiveds[-1]}",)
        print(f"{color.Fore.GREEN}{dir_count} Directories archived:", end=' ')
        print(f"{dt.now()}{color.Style.RESET_ALL}")
    else:
        print(f"{color.Fore.RED}{errors}\n{dt.now()}{color.Style.RESET_ALL}")
    return srctgtPaths

def clean(*args, **kwargs):
    pass

def mk_tgt_dir(*args, comment=None, direct:bool=False, **kwargs) -> str:
    tgtDirName = '' if direct else re.sub(r"([:. ])", r"-" , str(dt.now()))
    if comment is None:
        comment = input(f"Add a tgtDirName comment [10-72 chars]: ")
        msg = f"\n\ncomment must be 10 - 72 characters, but is {len(comment)}"
        assert 10 <= len(comment) <= 72, msg
    tgtDirName += f"_{re.sub(r'([:./ ])', r'_' , comment)}"
    return tgtDirName.strip('_')

def prep_target( *args, defaultTargets, target=None, **kwargs):
    # define archive targets
    targets = target if target is not None else defaultTargets
    for target in targets:
        if os.path.exists(os.path.join(target, 'archive')):
            break
    assert target, f"None of the required archive Targets was found: {targets}"
    tgtDir = os.path.join(target, 'archive', mk_tgt_dir(**kwargs))
    return tgtDir

def prep_paths(     tgtDir, *args,
                    defaultSources,
                    direct:bool=False,
                    rename:str=None,
                    sources=None, **kwargs) -> dict:

    # join sources and targets into a paths dictionary using fullPaths
    sources = sources if sources is not None else defaultSources
    paths = []
    for source in sources:
        sourcePath = os.path.expanduser(source)
        print(f"{color.Fore.YELLOW}sourcePath: {sourcePath}{color.Style.RESET_ALL}")
        if not os.path.exists(sourcePath):
            print(f"{color.Fore.RED}\nSource not found: {sourcePath}{color.Style.RESET_ALL}")
        else:
            if direct: tgtDir, _, dirName = tgtDir.partition('archive')
            tgtName = os.path.split(sourcePath)[-1] if rename is None else rename
            paths.append((
                            os.path.normpath(sourcePath), 
                            os.path.normpath(os.path.join(tgtDir, tgtName))
                            )
            )
    return paths

def get_parameter(fileName='params.yml', *args, **kwargs):
    with open(os.path.join(os.path.split(__file__)[0], fileName), 'r') as f:
        params = yaml.safe_load(f)
    return params

def main(*args, **kwargs):
    # kwargs = arguments.mk_args().__dict__
    params = get_parameter(**kwargs)
    tgtDir = prep_target(**kwargs, **params)
    srctgtPaths = archive(prep_paths(tgtDir, **params, **kwargs), params['ignore_dirs'])
