# finder.py
import os, re, time
from datetime import datetime as dt
import subprocess
import colorama as color
color.init()
import argparse

def find_changed(*args, startDir, days, projectName, verbose:int=0, **kwargs):
    assert days is not None, f"days must not be {days}"
    if projectName == 'all': projectName = None
    print(f"Searching with: {startDir, days, projectName}")
    gitDir, gitDirs = 'None', set()
    for i, (_dir, dirs, files) in enumerate(os.walk(os.path.expanduser(startDir))):
        if projectName is not None and not projectName in _dir: continue
        if not files: continue
        if '__' in _dir: continue
        if not any([re.search(r'.*\.\w{2,4}', f) for f in files]): continue
        if '.git' in dirs:
            gitDirs.add(_dir)
            gitDir = _dir
            if verbose: print(f"{[d.replace(startDir, '$startDir') for d in gitDirs] = }")
        elif any([_ds in _dir for _ds in gitDirs]):
            pass
        else:
            gitDir = None
        for file in files:
            filePath = os.path.join(_dir, file)
            daysUnchanged = ((dt.now() - dt.fromtimestamp(os.stat(filePath).st_mtime)).days)
            if daysUnchanged <= days:
                try:
                    if gitDir is not None:
                        if verbose: print(f"\trunning git diff for {gitDir = } -> {file}: {daysUnchanged}")
                        r = subprocess.run(['git', 'diff', filePath], shell=True, cwd=gitDir, stdout=subprocess.PIPE)
                        if r.returncode == 0:
                            out = r.stdout.decode('utf-8').replace('\n', '\n\t')
                            if out:
                                msg = f"{file} was changed {daysUnchanged} ago ! path: {gitDir}"
                                print(f"{color.Fore.YELLOW}{msg}{color.Style.RESET_ALL}", end='')
                                print(f"\n\tgit dff: {out}")
                except Exception as e:
                    print(f"{e = }")




def mk_args():
    parser = argparse.ArgumentParser(description="run: python finder.py -p startDir -d days -pr projectName")
    parser.add_argument(
        "-p",
        "--startDir",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=os.getcwd(),
        help="startDir to scan",
    )

    parser.add_argument(
        "-d",
        "--days",
        required=False,
        nargs=None,
        const=None,
        type=int,
        default=None,
        help="number of days to look back ",
    )

    # currently not used but should be used in upload instead of host
    parser.add_argument(
        "-n",
        "--projectName",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help="project to look inside"
    )
    parser.add_argument('-v', 
        '--verbose', 
        nargs='?', 
        const=True, 
        type=bool, 
        help='verbose'
    )
    return parser.parse_args()

def main(*args, **kwargs):
    find_changed(*args, **kwargs)


if __name__ == '__main__':
    main(**mk_args().__dict__)
