"""
script_path: src/protolib/core/creator/sync.py
description: >-
  Copies framework-scope files from an upstream protolib source into the current package clone.
  Preserves relative paths and rewrites caller-to-target identity parameters for absolute
  imports. Writes a sync log and recursively triggers synchronization in registered clones.
tags:
- cli
- infra
- sync
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
    description: Copies framework-scope files from an upstream source package to self.
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
        copied = self._apply(*args, **kwargs)
        return {"copied": copied}

    def _apply(self, *args, **kwargs) -> list:
        copied = []
        for scope in self.SYNC_SCOPE:
            copied.extend(self._sync_scope(*args, scope=scope, **kwargs))
        return copied

    def _sync_scope(self, *args, scope: str, **kwargs) -> list:
        scope_dir = os.path.join(self.source_dir, scope)
        if not os.path.isdir(scope_dir):
            return []
        rels = self._iter_rels(scope_dir, *args, **kwargs)
        return [r for r in rels if self._copy(*args, rel=r, **kwargs)]

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

def _sync_to_clone(*args, entry: dict, verbose: int = 0, **kwargs) -> dict:
    """description: Sync sts.package_dir to a single registered clone."""
    target = str(Path(entry["path"]) / "src" / entry["name"])
    s = Synchronizer(source_dir=sts.package_dir, target_dir=target, verbose=verbose)
    report = s.sync(*args, **kwargs)
    print(f"  {entry['name']}: {len(report['copied'])} file(s) synced.")
    return report

def _sync_registered(*args, **kwargs) -> dict:
    """description: Sync sts.package_dir to all registered clones. Cleans stale paths."""
    entries = _purge_stale(Clones(*args, **kwargs), *args, **kwargs)
    if not entries:
        print("No registered clones.")
        return {}
    return {e["name"]: _sync_and_recurse(*args, entry=e, **kwargs) for e in entries}

def _purge_stale(clones, *args, **kwargs) -> list:
    """description: Drop entries whose path no longer exists; return live entries."""
    live = [e for e in clones.load() if Path(e["path"]).exists()]
    for e in clones.load():
        if Path(e["path"]).exists(): continue
        clones.remove(e["path"])
        print(f"Removed stale entry: {e['path']}")
    return live

def _sync_and_recurse(*args, **kwargs) -> dict:
    """description: Sync, rewrite caller→target identity, write log, trigger child sync."""
    report = _sync_to_clone(*args, **kwargs)
    _transform_target(*args, **kwargs)
    _write_sync_log(*args, copied=report["copied"], **kwargs)
    _trigger_child_sync(*args, **kwargs)
    return report

def _transform_target(*args, entry: dict, **kwargs) -> None:
    """description: Rewrite caller→target identity across synced SYNC_SCOPE dirs."""
    target_root = str(Path(entry["path"]) / "src" / entry["name"])
    pkg_name = entry["name"]
    params = _build_rewrite_params(*args, target_root=target_root, pkg_name=pkg_name, **kwargs)
    if params is None: return
    for scope in Synchronizer.SYNC_SCOPE:
        _rewrite_scope(*args, target_root=target_root, scope=scope, params=params, **kwargs)

def _rewrite_scope(*args, target_root: str, scope: str, params, verbose: int = 0,
                   **kwargs) -> None:
    """description: Apply CloneParams text_repls to one scope dir inside the target."""
    scope_dir = os.path.join(target_root, scope)
    if not os.path.isdir(scope_dir): return
    v = verbose  # local alias — avoids K=K forwarding violation
    tx = TreeTransformer(scope_dir, *args, ignore_dirs=sts.ignore_dirs, verbose=v, **kwargs)
    tx.rewrite(params.text_repls())

def _build_rewrite_params(*args, **kwargs):
    """description: Load caller+target app settings; return CloneParams old=caller new=target."""
    tgt = _load_app_settings(*args, **kwargs)
    if tgt is None: return None
    caller = importlib.import_module(f"{sts.package_name}.app.settings")
    return CloneParams.from_settings(caller, *args, new_pr_name=tgt.project_name,
        new_pg_name=tgt.package_name, new_alias=getattr(tgt, "alias", None),
        new_port=getattr(tgt, "port", None), **kwargs)

def _load_app_settings(*args, target_root: str, pkg_name: str, **kwargs):
    """description: Load target's app/settings.py from disk; return None if absent."""
    path = Path(target_root) / "app" / "settings.py"
    if not path.exists(): return None
    spec = importlib.util.spec_from_file_location(f"_t.{pkg_name}.app.settings", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _write_sync_log(*args, entry: dict, copied: list, **kwargs) -> None:
    """description: Write ~/.{pkg}/sync_log.yaml with last_synced timestamp and files."""
    log_dir = Path.home() / f".{entry['name']}"
    log_dir.mkdir(parents=True, exist_ok=True)
    data = {"last_synced": datetime.now().isoformat(timespec="microseconds"),
            "synced_by": sts.package_name, "files": sorted(copied)}
    (log_dir / "sync_log.yaml").write_text(yaml.dump(data, default_flow_style=False))

def _trigger_child_sync(*args, entry: dict, **kwargs) -> None:
    """description: Run `<target-alias>-admin sync` inside the clone to propagate further."""
    target_root = str(Path(entry["path"]) / "src" / entry["name"])
    tgt = _load_app_settings(*args, target_root=target_root, pkg_name=entry["name"], **kwargs)
    alias = getattr(tgt, "alias", "proto") if tgt else "proto"
    print(f"  {entry['name']}: recursing...")
    subprocess.run(["uv", "run", f"{alias}-admin", "sync"], cwd=entry["path"])

def main(*args, **kwargs) -> dict:
    """description: Run gate, then push core/+helpers/ to all registered clones."""
    run_gate(sts.project_dir, *args, **kwargs)
    return _sync_registered(*args, **kwargs)


if __name__ == "__main__":
    main()
