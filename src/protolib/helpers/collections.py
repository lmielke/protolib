"""
script_path: src/protolib/helpers/collections.py
description: >-
  Provides stateless utility functions for path resolution, dictionary traversal, and text
  formatting within the protolib framework. Expands path aliases and resolves relative segments
  against the current working directory. Recursively searches nested dictionaries and wraps
  text for tabular display. Consumed by framework modules requiring standardized file lookup
  and data inspection.
tags:
- cli
- infra
- parsing
governance_exceptions:
- c8: no class definition — verify OOP intent
update_rules: Do not modify in clones.
"""
import os, re, textwrap, yaml
from pathlib import Path
from contextlib import contextmanager

import protolib.app.settings as sts

def _resolve_dots(wp:str, *args, **kwargs):
    """
    description: or .. relative to cwd.
    """
    if wp.startswith(".."):
        return os.path.join(os.path.dirname(os.getcwd()), wp[3:])
    if wp.startswith("."):
        return os.path.join(os.getcwd(), wp[2:])
    return wp

def unalias_path(wp:str, *args, **kwargs):
    """
    description: ~ %USERPROFILE%) with absolute paths.
    """
    if not any(c in wp for c in ".~%"):
        return wp
    wp = wp.replace(r"%USERPROFILE%", "~").replace("~", os.path.expanduser("~"))
    wp = _resolve_dots(wp, *args, **kwargs)
    return os.path.normpath(os.path.abspath(wp))

def prep_path(wp:str, *args, **kwargs):
    """
    description: Resolve path aliases and try common extensions if file not found.
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
    description: Recursively search nested dict for a key matching matcher.
    """
    for k, v in d.items():
        if k == matcher: return {k: v}
        if isinstance(v, dict):
            r = find_dict_entry(v, matcher, *args, **kwargs)
            if r: return r
    return None

def group_text(text, charLen, *args, **kwargs):
    """
    description: Wrap text or list of strings to charLen width.
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
    description: Walk source tree collecting dirs that match any regex in ignore_dirs.
    """
    regexs = [re.compile(d) for d in ignore_dirs]
    paths = (os.path.join(r, d).replace(os.sep, '/')
             for r, dirs, _ in os.walk(source, topdown=True) for d in dirs)
    return {os.path.normpath(p) for p in paths if any(r.search(p) for r in regexs)}

@contextmanager
def temp_chdir(target_dir, *args, **kwargs):
    """
    description: 'Context manager: temporarily change cwd, restore on exit.'
    """
    original_dir = os.getcwd()
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(original_dir)

def _is_ignored_dir(name, *args, **kwargs):
    """
    description: Check if directory name matches any pattern in sts.ignore_dirs.
    """
    name = name.strip()
    return any(name == i or name.endswith(i.strip('*')) for i in sts.ignore_dirs)

def _walk_for_file(file_name, pr_dir, max_depth, *args, **kwargs):
    root_depth = pr_dir.count(os.sep)
    for root, dirs, files in os.walk(pr_dir, topdown=True):
        depth_exceeded = root.count(os.sep) - root_depth >= max_depth
        if _should_skip_dir(*args, root=root, dirs=dirs, depth_exceeded=depth_exceeded, **kwargs):
            continue
        if file_name in files: return os.path.join(root, file_name)
        dirs[:] = [d for d in dirs if not _is_ignored_dir(d, *args, **kwargs)]
    return None

def _should_skip_dir(*args, root, dirs, depth_exceeded, **kwargs):
    if _is_ignored_dir(os.path.basename(root), *args, **kwargs) or depth_exceeded:
        dirs.clear()
        return True
    return False

def _find_file_path(raw_path=None, *args, project_dir=None, max_depth=5, **kwargs):
    """
    description: Locate a file by name within the project tree.
    """
    if not raw_path:
        return None
    pr_dir = project_dir or sts.project_dir
    return _walk_for_file(os.path.basename(raw_path), pr_dir, max_depth, *args, **kwargs)

_DS_SCHEMA = Path('~/.governance/docstring_templates.yml').expanduser()

def _validate_ds_scope(*args, scope, v, **kwargs):
    """
    description: Validate one docstring schema scope; raise ValueError naming scope on drift.
    """
    if not isinstance(v, dict):
        raise ValueError(f"scope {scope!r}: expected dict, got {type(v).__name__}")
    if not isinstance(v.get('required'), dict):
        raise ValueError(f"scope {scope!r}: 'required' must be a dict")
    opt = v.get('optional')
    if opt is not None and not isinstance(opt, dict):
        raise ValueError(f"scope {scope!r}: 'optional' must be a dict or null")

def load_docstring_schema(*args, **kwargs) -> dict:
    """
    description: Load allowed and required docstring keys per scope from the canonical YAML.
    """
    raw = yaml.safe_load(_DS_SCHEMA.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"docstring schema {_DS_SCHEMA}: expected top-level dict, got {type(raw).__name__}")
    for scope, v in raw.items(): _validate_ds_scope(*args, scope=scope, v=v, **kwargs)
    return {s: {'allowed': set(v['required']) | set(v.get('optional') or {}),
                'required': set(v['required'])} for s, v in raw.items()}
