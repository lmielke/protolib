"""
script_path: src/protolib/helpers/dir_context.py
description: >-
  DirContext resolves a file path into workspace, project, and package boundaries using marker
  files like pyproject.toml. It extracts AST symbols such as class and method names at a given
  cursor position. The dataclass emits legacy keyword arguments and snapshots for downstream
  tooling that needs project-relative context.
tags:
- infra
- parsing
- settings
update_rules: Do not modify in clones.
"""
from __future__ import annotations
import os, ast, sys
from dataclasses import dataclass, field


_SNAPSHOT_KEYS = [
    "work_dir", "project_dir", "package_dir", "is_package",
    "pr_name", "pg_name", "file_path", "file_name", "file_dir",
    "is_test_file", "import_path", "test_cmd", "class_name",
    "method_name", "project_key", "package_key",
]


@dataclass
class DirContext:
    """
    description: 'Resolves a file path into workspace, project, and package boundaries;
        extracts AST symbols at a cursor position and emits legacy kwargs for downstream tooling.'
    """
    # core
    work_dir: str | None = None
    project_dir: str | None = None
    package_dir: str | None = None
    is_package: bool = False
    pr_name: str | None = None
    pg_name: str | None = None
    # file facet
    file_path: str | None = None
    file_name: str | None = None
    file_dir: str | None = None
    is_test_file: bool = False
    import_path: str | None = None
    test_cmd: str | None = None
    class_name: str | None = None
    method_name: str | None = None
    # config
    project_key: str = "pyproject.toml"
    package_key: str = "__main__.py"
    # constructor shortcut
    path: str | None = field(default=None, repr=False, compare=False)
    cursor_pos: int | None = field(default=None, repr=False, compare=False)

    def __post_init__(self, *args, **kwargs):
        """description: 'Trigger full resolution pipeline when path is provided at construction time.'"""
        if self.path is None:
            return
        abs_path = self._abs_path(self.path, *args, **kwargs)
        self._resolve_workspace(abs_path, *args, **kwargs)
        self._resolve_file(abs_path, *args, **kwargs)
        self._resolve_names(*args, **kwargs)

    def _resolve_workspace(self, abs_path, *args, **kwargs):
        """description: 'Derive work_dir, project_dir, package_dir, and is_package from abs_path.'"""
        self.work_dir = self._derive_work_dir(abs_path, *args, **kwargs)
        self.project_dir = self._find_root(self.work_dir, self.project_key, *args, **kwargs)
        self.package_dir = self._find_package_dir(
            self.project_dir or self.work_dir, self.package_key, *args, **kwargs)
        self.is_package = self.package_dir is not None

    def _resolve_file(self, abs_path, *args, **kwargs):
        """description: 'Populate file facet fields, AST symbols, is_test_file, import_path, and test_cmd.'"""
        self.file_path, self.file_name, self.file_dir = self._file_facet(abs_path, *args, **kwargs)
        self.class_name, self.method_name = self._ast_symbols(
            self.file_path, self.cursor_pos, *args, **kwargs)
        self.is_test_file = bool(self.file_name and self.file_name.startswith("test"))
        self.import_path = self._import_path(self.file_path, self.project_dir, *args, **kwargs)
        self.test_cmd = self._test_cmd(self.file_path, self.project_dir, *args, **kwargs)

    def _resolve_names(self, *args, **kwargs):
        """description: 'Set pr_name and pg_name from project_dir and package_dir basenames.'"""
        self.pr_name = self._pkg_name(self.project_dir, self.is_package, *args, **kwargs)
        self.pg_name = self._pkg_name(self.package_dir, self.is_package, *args, **kwargs)

    # ---------- factories ----------
    @classmethod
    def __call__(cls, *args, path=None, cursor_pos=None, **kwargs):
        """description: 'Classmethod factory: resolve path and cursor_pos into a fully populated DirContext.'"""
        abs_path = cls._abs_path(path, *args, **kwargs)
        work_dir = cls._derive_work_dir(abs_path, *args, **kwargs)
        project_dir = cls._find_root(work_dir, cls.project_key, *args, **kwargs)
        pkg_dir = cls._find_package_dir(project_dir or work_dir, cls.package_key, *args, **kwargs)
        fp, fn, fd = cls._file_facet(abs_path, *args, **kwargs)
        cn, mn = cls._ast_symbols(fp, cursor_pos, *args, **kwargs)
        is_pkg = pkg_dir is not None
        return cls._build(work_dir, project_dir, pkg_dir, is_pkg, fp, fn, fd, cn, mn, *args, **kwargs)

    @classmethod
    def _build(cls, work_dir, project_dir, pkg_dir, is_pkg, fp, fn, fd, cn, mn,
               *args, **kwargs):
        """
        description: Assemble DirContext instance from resolved components.
        """
        extras = cls._derived(project_dir, pkg_dir, fp, fn, is_pkg, *args, **kwargs)
        return cls(work_dir=work_dir, project_dir=project_dir, package_dir=pkg_dir,
                   is_package=is_pkg, file_path=fp, file_name=fn, file_dir=fd,
                   class_name=cn, method_name=mn, **extras)

    @classmethod
    def _derived(cls, project_dir, pkg_dir, fp, fn, is_pkg, *args, **kwargs):
        """description: 'Build extras dict of derived fields for _build: names, import_path, test_cmd.'"""
        return {"pr_name": cls._pkg_name(project_dir, is_pkg, *args, **kwargs),
                "pg_name": cls._pkg_name(pkg_dir, is_pkg, *args, **kwargs),
                "import_path": cls._import_path(fp, project_dir, *args, **kwargs),
                "test_cmd": cls._test_cmd(fp, project_dir, *args, **kwargs),
                "is_test_file": bool(fn and fn.startswith("test"))}

    # ---------- public API ----------
    def to_kwargs(self, *args, package_info=None, verbose=False, **kwargs):
        """description: 'Merge is_package and package_info flags into kwargs for downstream callers.'"""
        out = dict(**kwargs, is_package=self.is_package, package_info=bool(package_info))
        if not package_info: return out
        if self.is_package:
            out.update({k: True for k in package_info})
        else:
            self._to_kwargs_fallback(out, package_info, verbose, *args, **kwargs)
        return out

    def _to_kwargs_fallback(self, out, package_info, verbose, *args, **kwargs):
        """description: 'Warn when package_info is set but is_package is False; add pg_tree if requested.'"""
        if verbose:
            sys.stderr.write("WARNING: package_info set, but is_package is False!\n")
        if "pg_tree" in package_info:
            out["pg_tree"] = True

    def snapshot(self, *args, **kwargs):
        """description: 'Return a dict of all snapshot-key fields for serialization or diffing.'"""
        return {k: getattr(self, k) for k in _SNAPSHOT_KEYS}

    def refresh(self, *args, path=None, cursor_pos=None, **kwargs):
        """description: 'Return a fresh DirContext from path or current file_path/work_dir.'"""
        base_path = path or self.file_path or self.work_dir
        return type(self)(path=base_path, cursor_pos=cursor_pos)

    # ---------- helpers ----------
    @staticmethod
    def _pkg_name(path, is_pkg, *args, **kwargs):
        """description: 'Return basename of path when is_pkg is True, otherwise None.'"""
        return os.path.basename(path) if is_pkg and path else None

    @staticmethod
    def _abs_path(path, *args, **kwargs):
        """description: 'Return absolute path of path, or cwd when path is None.'"""
        return os.path.abspath(path) if path else os.path.abspath(os.getcwd())

    @staticmethod
    def _derive_work_dir(path, *args, **kwargs):
        """description: 'Return path itself if a directory, otherwise its parent dirname.'"""
        return path if os.path.isdir(path) else os.path.dirname(path)

    @staticmethod
    def _find_root(start_dir, key_file, *args, **kwargs):
        """description: 'Walk up from start_dir until key_file is found; return that directory or None.'"""
        cur, up = start_dir, os.path.dirname(start_dir)
        while cur != up:
            if key_file in os.listdir(cur):
                return cur
            cur, up = up, os.path.dirname(up)
        return None

    @staticmethod
    def _find_package_dir(root_or_work, key_file, *args, **kwargs):
        """description: 'Return first child directory containing key_file, or root_or_work itself if it does.'"""
        if not root_or_work: return None
        for n in os.listdir(root_or_work):
            p = os.path.join(root_or_work, n)
            if os.path.isdir(p) and key_file in os.listdir(p): return p
        if key_file in os.listdir(root_or_work): return root_or_work
        return None

    @staticmethod
    def _file_facet(path, *args, **kwargs):
        """description: 'Return (file_path, file_name, file_dir) tuple, or (None, None, None) for directories.'"""
        if os.path.isdir(path):
            return None, None, None
        return path, os.path.basename(path), os.path.dirname(path)

    @staticmethod
    def _import_path(file_path, root_dir, *args, **kwargs):
        """description: 'Compute dotted import path of file_path relative to root_dir, or None if outside.'"""
        if not file_path or not root_dir:
            return None
        af, ar = os.path.abspath(file_path), os.path.abspath(root_dir)
        if not af.startswith(ar):
            return None
        rel = af[len(ar):].lstrip(os.path.sep)
        return os.path.splitext(rel)[0].replace(os.path.sep, ".")

    @staticmethod
    def _test_cmd(file_path, root_dir, *args, **kwargs):
        """description: 'Build a python -m unittest invocation for file_path relative to root_dir.'"""
        if not file_path or not root_dir:
            return None
        rel = os.path.splitext(file_path[len(root_dir):].lstrip(os.path.sep))[0]
        return f"python -m unittest {rel.replace(os.path.sep, '.')}"

    @staticmethod
    def _ast_symbols(file_path, cursor_pos, *args, **kwargs):
        """description: 'Parse file and return (class_name, method_name) at cursor_pos, or (None, None).'"""
        if not file_path or cursor_pos is None:
            return None, None
        txt, tree = DirContext._parse_file(file_path)
        if txt is None:
            return None, None
        line = DirContext._line_idx(txt, cursor_pos)
        return DirContext._class_at_line(tree, line), DirContext._func_at_line(tree, line)

    @staticmethod
    def _parse_file(file_path, *args, **kwargs):
        """description: 'Read and AST-parse file_path; return (text, tree) or (None, None) on failure.'"""
        try:
            with open(file_path, encoding="utf-8") as f:
                txt = f.read()
            return txt, ast.parse(txt)
        except Exception:
            return None, None

    @staticmethod
    def _line_idx(text, pos, *args, **kwargs):
        """description: 'Return zero-based line index in text containing character offset pos.'"""
        cur = 0
        for i, ln in enumerate(text.splitlines(keepends=True)):
            if cur + len(ln) > pos:
                return i
            cur += len(ln)
        return max(0, len(text.splitlines()) - 1)

    @staticmethod
    def _class_at_line(tree, line, *args, **kwargs):
        """description: 'Return name of ClassDef node that spans line, or None.'"""
        for n in ast.walk(tree):
            if not isinstance(n, ast.ClassDef): continue
            e = max((b.lineno for b in n.body), default=n.lineno) - 1
            if n.lineno - 1 <= line <= e:
                return n.name
        return None

    @staticmethod
    def _func_at_line(tree, line, *args, **kwargs):
        """description: 'Return name of FunctionDef node that spans line, or None.'"""
        for n in ast.walk(tree):
            if not isinstance(n, ast.FunctionDef): continue
            e = max((b.lineno for b in n.body), default=n.lineno) - 1
            if n.lineno - 1 <= line <= e:
                return n.name
        return None

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "DirContext(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Short text showing resolved project and file name.'"""
        return f"DirContext(pr={self.pr_name}, file={self.file_name})"
