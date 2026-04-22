"""
script_path: src/protolib/core/creator/sync.py
purpose: >-
  Pulls core/ and helpers/ from an upstream protolib source into the current clone
  package.
description: |-
  Walks SYNC_SCOPE directories in the upstream source directly and copies
  each file, preserving relative paths. After copy, rewrites caller→target
  identity (pr_name/pg_name/alias/port) so absolute imports and aliases match
  the target. Writes a sync_log.yaml to the clone's ~/.{pkg}/ dir after each
  push, then recursively triggers sync in the clone.
"""
import importlib
import importlib.util
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

import protolib.core.settings as sts
from protolib.core.creator.clone import CloneParams
from protolib.core.creator.clones import Clones
from protolib.core.creator.gate import run_gate
from protolib.core.creator.tree_transform import TreeTransformer


class Synchronizer:
    """
    purpose: Copies framework-scope files from an upstream source package to self.
    """

    SYNC_SCOPE = ("core", "helpers", "test/core")

    def __init__(self, *args, source_dir, target_dir=None, verbose=0, **kwargs):
        self.source_dir = os.path.abspath(source_dir)
        self.target_dir = os.path.abspath(target_dir or sts.package_dir)
        self.verbose = verbose

    def sync(self, *args, **kwargs) -> dict:
        """
        purpose: Walk SYNC_SCOPE in source and copy each file to target.
        description: 'Returns {''copied'': [...]}.'
        """
        copied = self._apply()
        return {"copied": copied}

    def _apply(self, *args, **kwargs) -> list:
        copied = []
        for scope in self.SYNC_SCOPE:
            copied.extend(self._sync_scope(scope=scope))
        return copied

    def _sync_scope(self, *args, scope: str, **kwargs) -> list:
        scope_dir = os.path.join(self.source_dir, scope)
        if not os.path.isdir(scope_dir):
            return []
        return [rel for rel in self._iter_rels(scope_dir) if self._copy(rel=rel)]

    def _iter_rels(self, scope_dir: str, *args, **kwargs):
        for root, dirs, files in os.walk(scope_dir):
            dirs[:] = [d for d in dirs if d not in sts.ignore_dirs]
            for fname in files:
                rel = os.path.relpath(os.path.join(root, fname), self.source_dir)
                yield rel.replace(os.sep, "/")

    def _copy(self, *args, rel: str, **kwargs) -> bool:
        src, dst = os.path.join(self.source_dir, rel), os.path.join(self.target_dir, rel)
        if not os.path.exists(src): return False
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        if self.verbose >= 2: print(f"  synced: {rel}")
        return True

def _sync_to_clone(entry: dict, verbose: int, *args, **kwargs) -> dict:
    """purpose: Sync sts.package_dir to a single registered clone."""
    target = str(Path(entry["path"]) / "src" / entry["name"])
    s = Synchronizer(source_dir=sts.package_dir, target_dir=target, verbose=verbose)
    report = s.sync()
    print(f"  {entry['name']}: {len(report['copied'])} file(s) synced.")
    return report

def _sync_registered(*args, verbose: int = 0, **kwargs) -> dict:
    """purpose: Sync sts.package_dir to all registered clones. Cleans stale paths."""
    entries = _purge_stale(Clones())
    if not entries:
        print("No registered clones.")
        return {}
    return {e["name"]: _sync_and_recurse(e, verbose) for e in entries}

def _purge_stale(clones, *args, **kwargs) -> list:
    """purpose: Drop entries whose path no longer exists; return live entries."""
    live = [e for e in clones.load() if Path(e["path"]).exists()]
    for e in clones.load():
        if Path(e["path"]).exists(): continue
        clones.remove(e["path"])
        print(f"Removed stale entry: {e['path']}")
    return live

def _sync_and_recurse(entry: dict, verbose: int, *args, **kwargs) -> dict:
    """purpose: Sync, rewrite caller→target identity, write log, trigger child sync."""
    report = _sync_to_clone(entry, verbose)
    _transform_target(entry=entry, verbose=verbose)
    _write_sync_log(entry, report["copied"])
    _trigger_child_sync(entry)
    return report

def _transform_target(*args, entry: dict, verbose: int, **kwargs) -> None:
    """purpose: Rewrite caller→target identity across synced SYNC_SCOPE dirs."""
    target_root = str(Path(entry["path"]) / "src" / entry["name"])
    params = _build_rewrite_params(target_root=target_root, pkg_name=entry["name"])
    if params is None: return
    for scope in Synchronizer.SYNC_SCOPE:
        _rewrite_scope(target_root=target_root, scope=scope, params=params, verbose=verbose)

def _rewrite_scope(*args, target_root: str, scope: str, params, verbose: int,
                   **kwargs) -> None:
    """purpose: Apply CloneParams text_repls to one scope dir inside the target."""
    scope_dir = os.path.join(target_root, scope)
    if not os.path.isdir(scope_dir): return
    tx = TreeTransformer(scope_dir, ignore_dirs=sts.ignore_dirs, verbose=verbose)
    tx.rewrite(params.text_repls())

def _build_rewrite_params(*args, target_root: str, pkg_name: str, **kwargs):
    """purpose: Load caller+target app settings; return CloneParams old=caller new=target."""
    tgt = _load_app_settings(target_root=target_root, pkg_name=pkg_name)
    if tgt is None: return None
    caller = importlib.import_module(f"{sts.package_name}.app.settings")
    return CloneParams.from_settings(caller, new_pr_name=tgt.project_name,
        new_pg_name=tgt.package_name, new_alias=getattr(tgt, "alias", None),
        new_port=getattr(tgt, "port", None))

def _load_app_settings(*args, target_root: str, pkg_name: str, **kwargs):
    """purpose: Load target's app/settings.py from disk; return None if absent."""
    path = Path(target_root) / "app" / "settings.py"
    if not path.exists(): return None
    spec = importlib.util.spec_from_file_location(f"_t.{pkg_name}.app.settings", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _write_sync_log(entry: dict, copied: list, *args, **kwargs) -> None:
    """purpose: Write ~/.{pkg}/sync_log.yaml with last_synced timestamp and files."""
    log_dir = Path.home() / f".{entry['name']}"
    log_dir.mkdir(parents=True, exist_ok=True)
    data = {"last_synced": datetime.now().isoformat(timespec="microseconds"),
            "synced_by": sts.package_name, "files": sorted(copied)}
    (log_dir / "sync_log.yaml").write_text(yaml.dump(data, default_flow_style=False))

def _trigger_child_sync(entry: dict, *args, **kwargs) -> None:
    """purpose: Run `<target-alias>-admin sync` inside the clone to propagate further."""
    target_root = str(Path(entry["path"]) / "src" / entry["name"])
    tgt = _load_app_settings(target_root=target_root, pkg_name=entry["name"])
    alias = getattr(tgt, "alias", "proto") if tgt else "proto"
    print(f"  {entry['name']}: recursing...")
    subprocess.run(["uv", "run", f"{alias}-admin", "sync"], cwd=entry["path"])

def main(*args, verbose: int = 0, **kwargs) -> dict:
    """purpose: Run gate, then push core/+helpers/ to all registered clones."""
    run_gate(sts.project_dir)
    return _sync_registered(verbose=verbose)


if __name__ == "__main__":
    main()
