"""
script_path: src/protolib/helpers/collections.py
purpose: Path resolution, dict traversal, text grouping, and directory walk utilities.
description: |-
  Stateless utility functions shared across the protolib framework.
  Provides path alias expansion, recursive dict search, text wrapping
  for tabular display, directory ignore-pattern collection, and file
  lookup within the project tree.
update_rules: Do not modify in clones.
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""
import os, re, textwrap, yaml
from pathlib import Path
from contextlib import contextmanager

import protolib.app.settings as sts

def _resolve_dots(wp:str, *args, **kwargs):
    """
    purpose: Resolve leading .
    description: or .. relative to cwd.
    """
    if wp.startswith(".."):
        return os.path.join(os.path.dirname(os.getcwd()), wp[3:])
    if wp.startswith("."):
        return os.path.join(os.getcwd(), wp[2:])
    return wp

def unalias_path(wp:str, *args, **kwargs):
    """
    purpose: Replace path aliases (.
    description: ~ %USERPROFILE%) with absolute paths.
    """
    if not any(c in wp for c in ".~%"):
        return wp
    wp = wp.replace(r"%USERPROFILE%", "~").replace("~", os.path.expanduser("~"))
    wp = _resolve_dots(wp, *args, **kwargs)
    return os.path.normpath(os.path.abspath(wp))

def prep_path(wp:str, *args, **kwargs):
    """
    purpose: Resolve path aliases and try common extensions if file not found.
    """
    wp = unalias_path(wp, *args, **kwargs)
    if os.path.exists(wp): return wp
    name, ext = os.path.splitext(os.path.basename(wp))
    for e in ["", sts.eext, sts.fext]:
        c = unalias_path(f"{name}{e}", *args, **kwargs)
        if os.path.isfile(c): return c
    return f"{name}{ext}"

def find_dict_entry(d, matcher, *args, **kwargs):
    """
    purpose: Recursively search nested dict for a key matching matcher.
    """
    for k, v in d.items():
        if k == matcher: return {k: v}
        if isinstance(v, dict):
            r = find_dict_entry(v, matcher, *args, **kwargs)
            if r: return r
    return None

def group_text(text, charLen, *args, **kwargs):
    """
    purpose: Wrap text or list of strings to charLen width.
    """
    if not text:
        return "None"
    if isinstance(text, str):
        text = '\n'.join(textwrap.wrap(text, width=charLen))
    elif isinstance(text, list):
        text = "\n".join(textwrap.wrap("\n".join(text), width=charLen))
    return '\n' + text

def collect_ignored_dirs(source, ignore_dirs, *args, **kwargs):
    """
    purpose: Walk source tree collecting dirs that match any regex in ignore_dirs.
    """
    regexs = [re.compile(d) for d in ignore_dirs]
    paths = (os.path.join(r, d).replace(os.sep, '/')
             for r, dirs, _ in os.walk(source, topdown=True) for d in dirs)
    return {os.path.normpath(p) for p in paths if any(r.search(p) for r in regexs)}

@contextmanager
def temp_chdir(target_dir, *args, **kwargs):
    """
    purpose: 'Context manager: temporarily change cwd, restore on exit.'
    """
    original_dir = os.getcwd()
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(original_dir)

def _is_ignored_dir(name, *args, **kwargs):
    """
    purpose: Check if directory name matches any pattern in sts.ignore_dirs.
    """
    name = name.strip()
    return any(name == i or name.endswith(i.strip('*')) for i in sts.ignore_dirs)

def _walk_for_file(file_name, pr_dir, max_depth, *args, **kwargs):
    root_depth = pr_dir.count(os.sep)
    for root, dirs, files in os.walk(pr_dir, topdown=True):
        if _should_skip_dir(root=root, dirs=dirs, root_depth=root_depth, max_depth=max_depth):
            continue
        if file_name in files: return os.path.join(root, file_name)
        dirs[:] = [d for d in dirs if not _is_ignored_dir(d)]
    return None

def _should_skip_dir(*args, root, dirs, root_depth, max_depth, **kwargs):
    depth_exceeded = root.count(os.sep) - root_depth >= max_depth
    if _is_ignored_dir(os.path.basename(root)) or depth_exceeded:
        dirs.clear()
        return True
    return False

def _find_file_path(raw_path=None, *args, project_dir=None, max_depth=5, **kwargs):
    """
    purpose: Locate a file by name within the project tree.
    """
    if not raw_path:
        return None
    pr_dir = project_dir or sts.project_dir
    return _walk_for_file(os.path.basename(raw_path), pr_dir, max_depth)

_DS_SCHEMA = Path(__file__).parent.parent / 'core' / 'resources' / 'docstring_templates.yml'

def load_docstring_schema(*args, **kwargs) -> dict:
    """
    purpose: Load allowed and required docstring keys per scope from the canonical YAML.
    """
    raw = yaml.safe_load(_DS_SCHEMA.read_text())
    return {s: {'allowed': set(v['required']) | set(v.get('optional', {})),
                'required': set(v['required'])} for s, v in raw.items()}
