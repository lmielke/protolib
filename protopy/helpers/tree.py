# tree.py
"""
WHY: Minimal, consistent tree builder that honors sts.* settings:
- ignore_dirs (with globs), abrev_dirs, ignore_files (verbosity thresholds).
- Collects matched files and (optionally) dumps contents by verbosity.
- Colorization is optional and isolated.
"""

import contextlib, fnmatch, os, re
from colorama import Fore, Style
from typing import Set, List, Tuple, Dict, Iterable, Optional

from protopy.helpers.collections import temp_chdir as _temp_chdir
import protopy.settings as sts

styles_dict: Dict[str, Dict[str, Dict[str, object]]] = {
    "default": {
        "dir":  {"sym": "|--",  "col": f"{Fore.WHITE}"},
        "file": {"sym": "|-",   "col": f"{Fore.WHITE}"},
        "fold": {"sym": "▼",    "col": f"{Fore.YELLOW}"},
        "dir_disc":  {"sym": "▶...", "col": f"{Style.DIM}{Fore.WHITE}"},
        "file_disc": {"sym": "|...", "col": f"{Style.DIM}{Fore.WHITE}"},
        "ext":  {"sym": [".py"], "col": [f"{Fore.BLUE}"]},
    },
}


class Tree:
    file_types: Dict[str, str] = {
        ".py": "Python", ".yml": "YAML", ".yaml": "YAML",
        ".md": "Markdown", ".txt": "Text",
    }

    def __init__(self, *args, style: str = "default", **kwargs):
        """
        WHY: One Tree to render hierarchy, collect matches, and read content.
        """
        self._apply_style(*args, style=style, **kwargs)
        self.indent = "    "
        self.matched_files: List[str] = []
        self.loaded_files: List[str] = []
        self.verbose = self.handle_verbosity(*args, **kwargs)
        self._out: Optional[List[str]] = None

    def __call__(self, *args, **kwargs) -> dict:
        """
        WHY: Convenience wrapper that returns a dict payload.
        """
        tree, contents = self.mk_tree(*args, **kwargs)
        selected = self.load_matched_files(*args, **kwargs)
        return {
            "tree": tree,
            "contents": contents,
            "file_matches": list(self.matched_files),
            "selected_files": selected,
            "loaded_files": list(self.loaded_files),
        }

    # --- verbosity / style --------------------------------------------------

    def handle_verbosity(self, *args, verbose: int = 0, yes: bool = False, **kwargs) -> int:
        """
        WHY: Verbosity controls content-dump depth.
        -y / yes=True disables any interactive questions.
        """
        if yes:
            return verbose

        if verbose >= 7:
            print(f"{Fore.YELLOW}WARNING: {verbose = } "
                  f"Output might excede the console length!{Style.RESET_ALL}")
            cont = input("Continue with a selected verbosity? "
                         "[1, 2, ..., ENTER keeps current]: ")
            if cont.isdigit():
                return int(cont)
        return verbose


    def _apply_style(self, *args, style: str, **kwargs) -> None:
        st = styles_dict.get(style, styles_dict["default"])
        for name, style_map in st.items():
            for k, v in style_map.items():
                setattr(self, f"{name}_{k}", v)

        # --- public API ---------------------------------------------------------

    def mk_tree(self, *args, project_dir:str=None, max_depth:int=6, ignores:set=None,
        colorized: bool = False, **kwargs) -> tuple[str, str]:
        """
        WHY: Walk project_dir; print dir first, then dir-disc if truncated/ignored.
        """
        self.matched_files.clear()
        self.loaded_files.clear()
        prj = (project_dir or (args[0] if args and isinstance(args[0], str) else None)
               or getattr(sts, "project_dir", os.getcwd()))
        ign = set(ignores) if ignores else set(getattr(sts, "ignore_dirs", set()))
        tree, contents = ["## Hierarchy"], ["## File Contents"]
        self._out = tree
        base = prj.count(os.sep)
        for root, dirs, files in os.walk(prj, topdown=True):
            level = root.count(os.sep) - base
            sub = os.path.basename(root)
            ind = self.indent * level
            tree.append(f"{ind}{self.dir_sym}{self.fold_sym} {sub}")
            if self._is_ignored(sub, ign) or (max_depth is not None and level >= max_depth):
                dirs[:] = []
                tree.append(f"{ind}{self.indent}{self.dir_disc_sym}")
                continue
            self._emit_files(root, files, ind, level, contents, *args, **kwargs )
        tree.append("\n")
        contents.append("\n")
        self._promote_workfile(*args, **kwargs)
        out = "\n".join(tree)
        if colorized:
            out = self._colorize(out, *args, **kwargs)
        return out, "\n".join(contents)

    def _emit_files(self, root: str, files: str, ind: str, level: int, contents: list, *args,
        file_match_regex = None, **kwargs) -> None:
        log_dir = self._is_abbrev_dir(root, *args, **kwargs)
        listed = 0
        for f in files:
            if log_dir and listed >= 1:
                self._line(f"{ind}{self.indent}{self.dir_disc_sym}", *args, **kwargs)
                break
            self._line(f"{ind}{self.indent}{self.file_sym} {f}", *args, **kwargs)
            full = os.path.join(root, f)
            if file_match_regex and re.search(file_match_regex, f):
                self._track_match(*args, path=full, **kwargs)
            should_load = self.verbose > level and not self._ignored_file(f, *args, **kwargs)
            if should_load:
                fc = self.load_file_content(*args, file_path=full, **kwargs)
                self.loaded_files.append(full)
                contents.append(
                    f"{Fore.CYAN}\n<file name='{f}' path='{full}'>{Fore.RESET}\n{fc}"
                )
            listed += 1

    def _track_match(self, *args, path: str | None = None, **kwargs) -> None:
        if path and path not in self.matched_files:
            self.matched_files.append(path)

    def _promote_workfile(self, *args, work_file_name:str=None, **kwargs) -> None:
        if not work_file_name:
            return
        idx = next(
            (i for i, p in enumerate(self.matched_files)
             if os.path.splitext(os.path.basename(p))[0] == work_file_name),
            None,
        )
        if idx is None:
            return
        p = self.matched_files.pop(idx)
        self.matched_files.insert(0, p)

    def load_matched_files(
        self,
        *args,
        default_ignore_files: Iterable[str] | None = None,
        **kwargs,
    ) -> List[dict]:
        """
        WHY: Load content for matched files; optional path-prefix filter.
        """
        sel: List[dict] = []
        prefixes = tuple(default_ignore_files or ())
        for p in self.matched_files:
            if prefixes and p.startswith(prefixes):
                continue
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    c = fh.read()
            except UnicodeDecodeError:
                print(f"{Fore.RED}Error reading file: {p}{Fore.RESET}")
                continue
            ext = os.path.splitext(p)[1]
            ftype = self.file_types.get(ext, "Text")
            sel.append({"file_path": p, "file_type": ftype, "file_content": c})
        return sel

    # --- helpers: ignore / abbrev / IO -------------------------------------

    def _is_ignored(self, subdir: str, ignores: Set[str], *args, **kwargs) -> bool:
        """
        WHY: Support exact matches, suffix-like, and glob patterns.
        """
        return any(
            subdir == pat
            or subdir.endswith(pat.lstrip("*"))
            or fnmatch.fnmatch(subdir, pat)
            for pat in ignores
        )

    def _match_pat(self, *args, f: str, p: str, **kwargs) -> bool:
        """Short matcher: exact, substring, or extension token like '.png'."""
        f2, p2 = f.casefold(), p.casefold()
        if p2.startswith(".") and "." in f2:
            return f2.endswith(p2)
        return p2 == f2 or p2 in f2

    def _ignored_file(self, fname: str, *args, **kwargs) -> bool:
        """
        Hide file contents until verbosity reaches the configured min level.
        Rule: if verbose < level_for_pattern and pattern in name -> ignore.
        """
        rules: dict[int, set[str]] = getattr(sts, "ignore_files", {})
        f = fname.casefold()
        return any(
            self.verbose < level and any(p.casefold() in f for p in pats)
            for level, pats in rules.items()
        )


    def _is_abbrev_dir(self, root: str, *args, **kwargs) -> bool:
        """
        WHY: Abbreviate directory listing if leaf name is in sts.abrev_dirs.
        """
        sub = os.path.basename(root)
        abr = set(getattr(sts, "abrev_dirs", set()))
        return sub in abr

    def load_file_content(self, *args, file_path: str, **kwargs) -> str:
        """
        WHY: Read file as text, suppress noisy errors unless verbose>=1.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            if self.verbose >= 1:
                print(f"{Fore.RED}Read error:{Fore.RESET} {e}")
            return ""

    def _line(self, s: str, *args, **kwargs) -> None:
        """
        WHY: Append a rendered line to the active tree buffer.
        """
        buf = getattr(self, "_out", None)
        if buf is not None:
            buf.append(s)

    # --- color / normalize / parse / mk-dirs --------------------------------

    def _colorize(self, tree: str, *args, style: str = "default", **kwargs) -> str:
        """
        WHY: Inject ANSI colors based on style symbols and file extensions.
        """
        st = styles_dict.get(style, styles_dict["default"])
        out: List[str] = []
        for line in tree.split("\n"):
            for name, m in st.items():
                sym, col = m.values()
                if name == "ext":
                    for sfx, c in zip(sym, col):
                        line = re.sub(
                            rf"(\S*{re.escape(sfx)})",
                            f"{c}\\1{Style.RESET_ALL}",
                            line,
                        )
                else:
                    line = line.replace(sym, f"{col}{sym}{Style.RESET_ALL}")
            out.append(line)
        return "\n".join(out).strip()
