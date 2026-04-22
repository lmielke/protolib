"""
script_path: src/protolib/helpers/tree.py
purpose: >-
  Tree builder that walks a project directory, collects matched files, and optionally
  dumps content.
description: |-
  Minimal, consistent tree builder that honors sts.* settings:
  ignore_dirs (with globs), abrev_dirs, ignore_files (verbosity thresholds).
  Collects matched files and optionally dumps contents by verbosity level.
  Colorization is optional and isolated via _colorize.
update_rules: Do not modify in clones.
"""

import contextlib, fnmatch, os, re, sys
from colorama import Fore, Style

from protolib.helpers.collections import temp_chdir as _temp_chdir
import protolib.app.settings as sts

styles_dict = {
    "default": {
        "dir":  {"sym": "|--",  "col": f"{Fore.WHITE}"},
        "file": {"sym": "|-",   "col": f"{Fore.WHITE}"},
        "fold": {"sym": "\u25bc",    "col": f"{Fore.YELLOW}"},
        "dir_disc":  {"sym": "\u25b6...", "col": f"{Style.DIM}{Fore.WHITE}"},
        "file_disc": {"sym": "|...", "col": f"{Style.DIM}{Fore.WHITE}"},
        "ext":  {"sym": [".py"], "col": [f"{Fore.BLUE}"]},
    },
}


class Tree:
    file_types = {
        ".py": "Python", ".yml": "YAML", ".yaml": "YAML",
        ".md": "Markdown", ".txt": "Text",
    }
    TREE_HEADER = "## Hierarchy"
    CONTENTS_HEADER = "## File Contents"

    def __init__(self, *args, style="default", **kwargs):
        self._apply_style(*args, style=style, **kwargs)
        self.indent = "    "
        self.matched_files = []
        self.loaded_files = []
        self.verbose = self.handle_verbosity(*args, **kwargs)
        self._out, self._contents = None, None

    def __call__(self, *args, **kwargs):
        tree, contents = self.mk_tree(*args, **kwargs)
        selected = self.load_matched_files(*args, **kwargs)
        return {
            "tree": tree, "contents": contents,
            "file_matches": list(self.matched_files),
            "selected_files": selected,
            "loaded_files": list(self.loaded_files),
        }

    # --- verbosity / style ---------------------------------------------------

    def handle_verbosity(self, *args, verbose=0, yes=False, **kwargs):
        if yes or verbose < 7:
            return verbose
        return self._ask_verbosity(*args, verbose=verbose, **kwargs)

    def _ask_verbosity(self, *args, verbose=0, **kwargs):
        msg = (f"{Fore.YELLOW}WARNING: {verbose = } "
               f"Output might excede the console length!{Style.RESET_ALL}\n")
        sys.stderr.write(msg)
        cont = input("Continue? [1..N, ENTER keeps current]: ")
        return int(cont) if cont.isdigit() else verbose

    def _apply_style(self, *args, style="default", **kwargs):
        st = styles_dict.get(style, styles_dict["default"])
        for name, style_map in st.items():
            for k, v in style_map.items():
                setattr(self, f"{name}_{k}", v)

    # --- public API ----------------------------------------------------------

    def mk_tree(self, *args, project_dir=None, max_depth=6, ignores=None,
                colorized=False, **kwargs):
        self._reset_buffers()
        prj = self._resolve_project_dir(*args, project_dir=project_dir, **kwargs)
        ign = set(ignores) if ignores else set(getattr(sts, "ignore_dirs", set()))
        self._walk(prj, ign, max_depth, *args, **kwargs)
        self._finalize(*args, colorized=colorized, **kwargs)
        return "\n".join(self._out), "\n".join(self._contents)

    def _reset_buffers(self, *args, **kwargs):
        self.matched_files.clear()
        self.loaded_files.clear()
        self._out = [self.TREE_HEADER]
        self._contents = [self.CONTENTS_HEADER]

    def _resolve_project_dir(self, *args, project_dir=None, **kwargs):
        if project_dir:
            return project_dir
        if args and isinstance(args[0], str):
            return args[0]
        return getattr(sts, "project_dir", os.getcwd())

    def _walk(self, prj, ign, max_depth, *args, **kwargs):
        base = prj.count(os.sep)
        for root, dirs, files in os.walk(prj, topdown=True):
            level, sub = root.count(os.sep) - base, os.path.basename(root)
            ind = self.indent * level
            self._out.append(f"{ind}{self.dir_sym}{self.fold_sym} {sub}")
            if self._truncate_if_skipped(sub, ign, level, max_depth, dirs, ind): continue
            self._emit_files(root, files, ind, level, *args, **kwargs)

    def _truncate_if_skipped(self, sub, ign, level, max_depth, dirs, ind, *args, **kwargs):
        skip = self._is_ignored(sub, ign) or (max_depth is not None and level >= max_depth)
        if skip:
            dirs[:] = []
            self._out.append(f"{ind}{self.indent}{self.dir_disc_sym}")
        return skip

    def _finalize(self, *args, colorized=False, **kwargs):
        self._out.append("\n")
        self._contents.append("\n")
        self._promote_workfile(*args, **kwargs)
        if colorized:
            colored = self._colorize("\n".join(self._out), *args, **kwargs)
            self._out.clear()
            self._out.extend(colored.split("\n"))

    def _emit_files(self, root, files, ind, level, *args, **kwargs):
        log_dir = self._is_abbrev_dir(root, *args, **kwargs)
        for i, f in enumerate(files):
            if log_dir and i >= 1:
                self._out.append(f"{ind}{self.indent}{self.dir_disc_sym}")
                break
            self._emit_one_file(root, f, ind, level, *args, **kwargs)

    def _emit_one_file(self, root, f, ind, level, *args, file_match_regex=None, **kwargs):
        self._out.append(f"{ind}{self.indent}{self.file_sym} {f}")
        full = os.path.join(root, f)
        if file_match_regex and re.search(file_match_regex, f):
            self._track_match(*args, path=full, **kwargs)
        self._maybe_load(f, full, level, *args, **kwargs)

    def _maybe_load(self, fname, full, level, *args, **kwargs):
        if self.verbose <= level or self._ignored_file(fname, *args, **kwargs): return
        fc = self.load_file_content(*args, file_path=full, **kwargs)
        self.loaded_files.append(full)
        self._contents.append(
            f"{Fore.CYAN}\n<file name='{fname}' path='{full}'>{Fore.RESET}\n{fc}")

    def _track_match(self, *args, path=None, **kwargs):
        if path and path not in self.matched_files:
            self.matched_files.append(path)

    def _promote_workfile(self, *args, work_file_name=None, **kwargs):
        if not work_file_name: return
        idx = next((i for i, p in enumerate(self.matched_files)
                    if os.path.splitext(os.path.basename(p))[0] == work_file_name), None)
        if idx is not None: self.matched_files.insert(0, self.matched_files.pop(idx))

    def load_matched_files(self, *args, default_ignore_files=None, **kwargs):
        prefixes = tuple(default_ignore_files or ())
        pairs = ((p, self._read_matched(p, *args, **kwargs)) for p in self.matched_files
                 if not (prefixes and p.startswith(prefixes)))
        return [{"file_path": p,
                 "file_type": self.file_types.get(os.path.splitext(p)[1], "Text"),
                 "file_content": c} for p, c in pairs if c is not None]

    def _read_matched(self, path, *args, **kwargs):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return fh.read()
        except UnicodeDecodeError:
            sys.stderr.write(f"{Fore.RED}Error reading file: {path}{Fore.RESET}\n")
            return None

    # --- helpers: ignore / abbrev / IO ----------------------------------------

    def _is_ignored(self, subdir, ignores, *args, **kwargs):
        return any(
            subdir == pat or subdir.endswith(pat.lstrip("*")) or fnmatch.fnmatch(subdir, pat)
            for pat in ignores
        )

    def _match_pat(self, *args, f="", p="", **kwargs):
        f2, p2 = f.casefold(), p.casefold()
        if p2.startswith(".") and "." in f2:
            return f2.endswith(p2)
        return p2 == f2 or p2 in f2

    def _ignored_file(self, fname, *args, **kwargs):
        rules = getattr(sts, "ignore_files", {})
        f = fname.casefold()
        return any(
            self.verbose < level and any(p.casefold() in f for p in pats)
            for level, pats in rules.items()
        )

    def _is_abbrev_dir(self, root, *args, **kwargs):
        sub = os.path.basename(root)
        return sub in set(getattr(sts, "abrev_dirs", set()))

    def load_file_content(self, *args, file_path="", **kwargs):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            if self.verbose >= 1:
                sys.stderr.write(f"{Fore.RED}Read error:{Fore.RESET} {e}\n")
            return ""

    # --- color ----------------------------------------------------------------

    def _colorize(self, tree, *args, style="default", **kwargs):
        st = styles_dict.get(style, styles_dict["default"])
        out = []
        for line in tree.split("\n"):
            line = self._colorize_line(line, st, *args, **kwargs)
            out.append(line)
        return "\n".join(out).strip()

    def _colorize_line(self, line, st, *args, **kwargs):
        for name, m in st.items():
            sym, col = m.values()
            if name == "ext":
                line = self._colorize_ext(line, sym, col, *args, **kwargs)
            else:
                line = line.replace(sym, f"{col}{sym}{Style.RESET_ALL}")
        return line

    def _colorize_ext(self, line, syms, cols, *args, **kwargs):
        for sfx, c in zip(syms, cols):
            line = re.sub(rf"(\S*{re.escape(sfx)})", f"{c}\\1{Style.RESET_ALL}", line)
        return line
