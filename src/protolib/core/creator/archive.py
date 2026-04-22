"""
script_path: src/protolib/core/creator/archive.py
purpose: Archive project directories with configurable ignore-pattern support.
description: |-
  Collects
  the list of directories to exclude from settings, prepares a timestamped target
  path, and copies the source tree using shutil. Produces a tabulated summary of
  archived paths. Do not modify in clones — synced from upstream protolib.
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""
import os, re, shutil, yaml
from datetime import datetime as dt
from tabulate import tabulate
import colorama as color
color.init()

def collect_ignored_dirs(source, ignore_dirs, *args, **kwargs):
    regexs = [re.compile(d) for d in ignore_dirs]
    paths = (os.path.join(r, d).replace(os.sep, '/')
             for r, dirs, _ in os.walk(source, topdown=True) for d in dirs)
    return {os.path.normpath(p) for p in paths if any(r.search(p) for r in regexs)}

def custom_ignore(ignored, *args, **kwargs):
    def _ignore_func(d, cs, *args, **kwargs):
        return {c for c in cs if os.path.join(d, c) in ignored}
    return _ignore_func

def archive(srctgtPaths, ignore_dirs=None, *args, **kwargs):
    errors, count = [], 0
    _print_header(srctgtPaths)
    rows = _table_rows(srctgtPaths)
    for i, (source, target) in enumerate(srctgtPaths):
        count, errors = _archive_one(source, target, ignore_dirs, count, errors, rows, i)
    _print_summary(errors, count, rows)
    return srctgtPaths

def _print_header(srctgtPaths, *args, **kwargs):
    rows = _table_rows(srctgtPaths)
    for line in rows[:3]:
        print(line)

def _table_rows(srctgtPaths, *args, **kwargs):
    return tabulate(srctgtPaths, headers=['source', 'target'],
                    tablefmt='psql', showindex=True).split('\n')

def _archive_one(source, target, ignore_dirs, count, errors, rows, i, *args, **kwargs):
    try:
        count += _do_copy(source, target, ignore_dirs)
        print(f"{color.Fore.WHITE}{rows[i + 3]}{color.Style.RESET_ALL}")
    except Exception as e:
        print(f"{color.Fore.RED}{rows[i + 3]} -> {e}{color.Style.RESET_ALL}")
        errors.append((source, target, e))
    return count, errors

def _do_copy(source, target, ignore_dirs, *args, **kwargs):
    ignored = collect_ignored_dirs(source, ignore_dirs)
    if os.path.isdir(source):
        return _copy_tree(source, target, ignored)
    if os.path.isfile(source):
        shutil.copyfile(source, target)
    return 0

def _copy_tree(source, target, ignored, *args, **kwargs):
    os.makedirs(target, exist_ok=True)
    count = 0
    for root, dirs, files in os.walk(source, topdown=True):
        dirs[:] = [d for d in dirs if os.path.normpath(os.path.join(root, d)) not in ignored]
        count += _copy_files(root, files, source, target, ignored)
    return count

def _copy_files(root, files, source, target, ignored, *args, **kwargs):
    srcs = [os.path.normpath(os.path.join(root, f)) for f in files]
    pairs = [(s, os.path.join(target, os.path.relpath(s, source)))
             for s in srcs if s not in ignored]
    for src, dest in pairs:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
    return len(pairs)

def _print_summary(errors, count, rows, *args, **kwargs):
    if errors:
        print(f"{color.Fore.RED}{errors}\n{dt.now()}{color.Style.RESET_ALL}")
        return
    print(rows[-1])
    print(f"{color.Fore.GREEN}{count} Directories archived: {dt.now()}{color.Style.RESET_ALL}")

def mk_tgt_dir(*args, comment=None, direct: bool = False, **kwargs) -> str:
    name = '' if direct else re.sub(r"([:. ])", r"-", str(dt.now()))
    if comment is None:
        comment = input("Add a tgtDirName comment [10-72 chars]: ")
        assert 10 <= len(comment) <= 72, f"comment must be 10-72 chars, got {len(comment)}"
    name += f"_{re.sub(r'([:./ ])', r'_', comment)}"
    return name.strip('_')

def prep_target(*args, defaultTargets, target=None, **kwargs):
    targets = target if target is not None else defaultTargets
    t = next((t for t in targets if os.path.exists(os.path.join(t, 'archive'))), None)
    assert t, f"No archive target found: {targets}"
    return os.path.join(t, 'archive', mk_tgt_dir(**kwargs))

def prep_paths(tgtDir, *args, defaultSources, direct=False, rename=None,
               sources=None, **kwargs):
    sources = sources if sources is not None else defaultSources
    paths = []
    for source in sources:
        entry = _prep_one_path(source, tgtDir, direct, rename)
        if entry:
            paths.append(entry)
    return paths

def _prep_one_path(source, tgtDir, direct, rename, *args, **kwargs):
    sp = os.path.expanduser(source)
    print(f"{color.Fore.YELLOW}sourcePath: {sp}{color.Style.RESET_ALL}")
    if not os.path.exists(sp):
        print(f"{color.Fore.RED}\nSource not found: {sp}{color.Style.RESET_ALL}")
        return None
    td = tgtDir.partition('archive')[0] if direct else tgtDir
    name = os.path.split(sp)[-1] if rename is None else rename
    return (os.path.normpath(sp), os.path.normpath(os.path.join(td, name)))

def get_parameter(*args, fileName='params.yml', **kwargs):
    with open(os.path.join(os.path.split(__file__)[0], fileName), 'r') as f:
        return yaml.safe_load(f)

def main(*args, **kwargs):
    params = get_parameter(**kwargs)
    tgtDir = prep_target(**kwargs, **params)
    archive(prep_paths(tgtDir, **params, **kwargs), params['ignore_dirs'])

if __name__ == '__main__':
    main()
