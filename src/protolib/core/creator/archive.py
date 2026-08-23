"""
script_path: src/protolib/core/creator/archive.py
description: >-
  Archives project directories by copying source trees to timestamped targets while excluding
  paths matching configured ignore patterns. Uses shutil for file operations and tabulate
  to render a summary table of archived paths. Consumed by the protolib creator module to
  snapshot project states.
tags:
- backup
- cli
- infra
"""
import os, re, shutil, yaml
from datetime import datetime as dt
from tabulate import tabulate
import colorama as color
color.init()


class Archiver:
    """
    description: |-
      Holds per-run state (errors, copy count, rendered table rows) and drives the
      archive loop. Pure copy helpers remain module-level functions. Call run() to
      execute; returns the original srctgtPaths list.
    """

    def __init__(self, srctgtPaths, ignore_dirs=None, *args, **kwargs):
        """description: 'Initialise run state and pre-render the tabulate table.'"""
        self.srctgtPaths = srctgtPaths
        self.ignore_dirs = ignore_dirs or []
        self._errors: list = []
        self._count: int = 0
        self._rows: list = tabulate(srctgtPaths, headers=['source', 'target'],
                                    tablefmt='psql', showindex=True).split('\n')

    def run(self, *args, **kwargs):
        """description: 'Print header, archive each pair, print summary; return srctgtPaths.'"""
        for line in self._rows[:3]:
            print(line)
        for i, (source, target) in enumerate(self.srctgtPaths):
            self._step(source, target, i, *args, **kwargs)
        self._summary(*args, **kwargs)
        return self.srctgtPaths

    def _step(self, source, target, i, *args, **kwargs):
        """description: 'Archive one (source, target) pair; accumulate errors and count.'"""
        try:
            self._count += _do_copy(source, target, self.ignore_dirs, *args, **kwargs)
            print(f"{color.Fore.WHITE}{self._rows[i + 3]}{color.Style.RESET_ALL}")
        except Exception as e:
            print(f"{color.Fore.RED}{self._rows[i + 3]} -> {e}{color.Style.RESET_ALL}")
            self._errors.append((source, target, e))

    def _summary(self, *args, **kwargs):
        """description: 'Print final status line; red on errors, green on success.'"""
        if self._errors:
            print(f"{color.Fore.RED}{self._errors}\n{dt.now()}{color.Style.RESET_ALL}")
            return
        print(self._rows[-1])
        print(f"{color.Fore.GREEN}{self._count} Directories archived: {dt.now()}{color.Style.RESET_ALL}")

    def __repr__(self, *args, **kwargs):
        """description: 'Developer repr showing path count and error state.'"""
        return f"Archiver(paths={len(self.srctgtPaths)}, errors={len(self._errors)})"

    def __str__(self, *args, **kwargs):
        """description: 'Human-readable summary of archive run state.'"""
        return self.__repr__(*args, **kwargs)

def archive(srctgtPaths, ignore_dirs=None, *args, **kwargs):
    """description: 'Public entry point — delegates to Archiver.run().'"""
    return Archiver(srctgtPaths, ignore_dirs, *args, **kwargs).run(*args, **kwargs)

def collect_ignored_dirs(source, ignore_dirs, *args, **kwargs):
    """description: 'Return set of normalised paths under source matching any ignore pattern.'"""
    regexs = [re.compile(d) for d in ignore_dirs]
    paths = (os.path.join(r, d).replace(os.sep, '/')
             for r, dirs, _ in os.walk(source, topdown=True) for d in dirs)
    return {os.path.normpath(p) for p in paths if any(r.search(p) for r in regexs)}

def custom_ignore(ignored, *args, **kwargs):
    """description: 'Return shutil ignore function that skips paths in the ignored set.'"""
    def _ignore_func(d, cs, *args, **kwargs):
        """description: 'Return subset of cs whose joined paths are in ignored set.'"""
        return {c for c in cs if os.path.join(d, c) in ignored}
    return _ignore_func

def _do_copy(source, target, ignore_dirs, *args, **kwargs):
    """description: 'Copy source (file or tree) to target, excluding ignored paths.'"""
    ignored = collect_ignored_dirs(source, ignore_dirs, *args, **kwargs)
    if os.path.isdir(source):
        return _copy_tree(source, target, ignored, *args, **kwargs)
    if os.path.isfile(source):
        shutil.copyfile(source, target)
    return 0

def _copy_tree(source, target, ignored, *args, **kwargs):
    """description: 'Recursively copy source tree to target, pruning ignored dirs.'"""
    os.makedirs(target, exist_ok=True)
    count = 0
    for root, dirs, files in os.walk(source, topdown=True):
        dirs[:] = [d for d in dirs if os.path.normpath(os.path.join(root, d)) not in ignored]
        count += _copy_files(root, files, source, target, ignored, *args, **kwargs)
    return count

def _copy_files(root, files, source, target, ignored, *args, **kwargs):
    """description: 'Copy non-ignored files in root, preserving relative structure.'"""
    srcs = [os.path.normpath(os.path.join(root, f)) for f in files]
    pairs = [(s, os.path.join(target, os.path.relpath(s, source)))
             for s in srcs if s not in ignored]
    for src, dest in pairs:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
    return len(pairs)

def mk_tgt_dir(*args, comment=None, direct: bool = False, **kwargs) -> str:
    """description: 'Build a timestamped target directory name with an optional comment.'"""
    name = '' if direct else re.sub(r"([:. ])", r"-", str(dt.now()))
    if comment is None:
        comment = input("Add a tgtDirName comment [10-72 chars]: ")
        assert 10 <= len(comment) <= 72, f"comment must be 10-72 chars, got {len(comment)}"
    name += f"_{re.sub(r'([:./ ])', r'_', comment)}"
    return name.strip('_')

def prep_target(*args, defaultTargets, target=None, **kwargs):
    """description: 'Find first existing archive root and append a timestamped subdirectory.'"""
    targets = target if target is not None else defaultTargets
    t = next((t for t in targets if os.path.exists(os.path.join(t, 'archive'))), None)
    assert t, f"No archive target found: {targets}"
    return os.path.join(t, 'archive', mk_tgt_dir(*args, **kwargs))

def prep_paths(tgtDir, *args, defaultSources, direct=False, rename=None,
               sources=None, **kwargs):
    """description: 'Resolve each source path and return (source, target) pairs.'"""
    sources = sources if sources is not None else defaultSources
    paths = []
    for source in sources:
        entry = _prep_one_path(source, tgtDir, direct, rename, *args, **kwargs)
        if entry:
            paths.append(entry)
    return paths

def _prep_one_path(source, tgtDir, direct, rename, *args, **kwargs):
    """description: 'Resolve one source to a (source, target) pair; None if source missing.'"""
    sp = os.path.expanduser(source)
    print(f"{color.Fore.YELLOW}sourcePath: {sp}{color.Style.RESET_ALL}")
    if not os.path.exists(sp):
        print(f"{color.Fore.RED}\nSource not found: {sp}{color.Style.RESET_ALL}")
        return None
    td = tgtDir.partition('archive')[0] if direct else tgtDir
    name = os.path.split(sp)[-1] if rename is None else rename
    return (os.path.normpath(sp), os.path.normpath(os.path.join(td, name)))

def get_parameter(*args, fileName='params.yml', **kwargs):
    """description: 'Load params.yml from the module directory and return as dict.'"""
    with open(os.path.join(os.path.split(__file__)[0], fileName), 'r') as f:
        return yaml.safe_load(f)

def main(*args, **kwargs):
    """description: 'CLI entry point: load params, resolve paths, run archiver.'"""
    params = get_parameter(*args, **kwargs)
    tgtDir = prep_target(*args, **params, **kwargs)
    archive(prep_paths(tgtDir, *args, **params, **kwargs), params['ignore_dirs'], *args, **kwargs)


if __name__ == '__main__':
    main()
