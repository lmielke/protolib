"""
script_path: src/protolib/core/creator/tree_transform.py
purpose: File-tree transformation primitives used by the clone utility.
description: |-
  Walks a project
  tree to rename matching files and directories, remove files matching patterns,
  substitute text with case-aware variants, strip lines marked for removal, and
  update the requires-python pin in pyproject.toml. All operations are idempotent
  and skip configured ignore_dirs (.git, .venv, etc.).
"""
import os, re, time
from colorama import Fore


class TreeTransformer:
    """
    purpose: Performs structural and content transformations on a project tree.
    """

    FILE_PATTERNS = [r'.*\.log$', r'.*\.lock$', r'.*\.tmp$', r'^temp.*']
    # REMOVE_MARKER: retained for capability but not invoked by the clone pipeline.
    # Self-similar template: clones receive the full source unmodified.
    REMOVE_MARKER = '# clone_remove_line'

    def __init__(self, project_path, *args, ignore_dirs=None, verbose=0, **kwargs):
        self.path = project_path
        self.ignore_dirs = ignore_dirs or set()
        self.verbose = verbose

    def restructure(self, file_rules: dict, *args, **kwargs) -> None:
        """
        purpose: 'Walk tree bottom-up: remove patterned files, rename files, then dirs.'
        """
        for root, dirs, files in os.walk(self.path, topdown=False):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            self.remove_files(root=root, files=files)
            self.rename_files(root=root, files=files, rules=file_rules)
            self.rename_dirs(root=root, dirs=dirs, rules=file_rules)

    def rewrite(self, text_repls: dict, *args, **kwargs) -> None:
        """
        purpose: 'Walk tree top-down: replace text in each file.'
        description: |-
          Marker stripping is disabled
                  under the self-similar template policy; remove_marked_lines remains callable.
        """
        for root, dirs, files in os.walk(self.path, topdown=True):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            self.replace_text(root=root, files=files, repls=text_repls)

    def set_pyproject_version(self, pyproject_path, py_version, *args, **kwargs):
        """
        purpose: Update requires-python in pyproject.toml to short(py_version).
        """
        if py_version is None: return
        short = ".".join(py_version.split(".")[:2])
        try: self._write_pyproject(path=pyproject_path, short=short)
        except FileNotFoundError:
            print(f"{Fore.RED}\tpyproject.toml not found at {pyproject_path}{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.RED}\tError updating {pyproject_path}: {e}{Fore.RESET}")

    def _write_pyproject(self, *args, path: str, short: str, **kwargs) -> None:
        with open(path, 'r') as f:
            new_lines, found = self._rewrite_lines(lines=f.readlines(), short=short)
        with open(path, 'w') as f:
            f.writelines(new_lines)
        if not found:
            print(f"{Fore.YELLOW}\t'requires-python' not found in {path}.{Fore.RESET}")

    @staticmethod
    def _rewrite_lines(*args, lines: list, short: str, **kwargs) -> tuple:
        out, found = [], False
        for line in lines:
            if line.strip().startswith('requires-python'):
                out.append(f'requires-python = ">={short}"\n')
                found = True
            else: out.append(line)
        return out, found

    def rename_files(self, *args, root: str, files: list, rules: dict, **kwargs) -> None:
        """
        purpose: Rename files whose stem contains an old_name from rules.
        """
        for fn in files:
            for old, new in rules.items():
                if new is None: continue
                if old not in os.path.splitext(fn)[0]: continue
                self._rename_one_file(root=root, fn=fn, old=old, new=new)
                break

    def _rename_one_file(self, root, fn, old, new, *args, **kwargs):
        old_p = os.path.join(root, fn)
        new_p = os.path.join(root, fn.replace(old, new))
        if os.path.exists(old_p) and old_p != new_p:
            if self.verbose >= 3:
                print(f"\t{Fore.BLUE}Rename file:{Fore.RESET} {old_p} to {new_p}")
            os.rename(old_p, new_p)

    def rename_dirs(self, *args, root: str, dirs: list, rules: dict, **kwargs) -> None:
        """
        purpose: Rename directories whose name exactly matches an old_name from rules.
        """
        renamed = set()
        for dn in list(dirs):
            self._try_rename_dir(root=root, dn=dn, rules=rules, renamed=renamed)

    def _try_rename_dir(self, *args, root, dn, rules, renamed, **kwargs):
        for old, new in rules.items():
            if new is None or dn != old or old in renamed: continue
            if self._rename_one_dir(root=root, old=old, new=new):
                renamed.add(new)
                return

    def _rename_one_dir(self, *args, root: str, old: str, new: str, **kwargs) -> bool:
        old_p, new_p = os.path.join(root, old), os.path.join(root, new)
        if os.path.exists(old_p) and old_p != new_p:
            if self.verbose >= 3:
                print(f"{Fore.BLUE}\tRename directory:{Fore.RESET} {old_p} to {new_p}")
            os.rename(old_p, new_p)
            return True
        return False

    def remove_files(self, root, files, *args, patterns=None, **kwargs):
        """
        purpose: Remove files in root whose name matches any of the given regex patterns.
        """
        pats = patterns if patterns is not None else self.FILE_PATTERNS
        for fn in files:
            if not any(re.match(p, fn) for p in pats): continue
            fp = os.path.join(root, fn)
            if os.path.exists(fp): self._remove_one(fp=fp, fn=fn)

    def _remove_one(self, *args, fp: str, fn: str, **kwargs) -> None:
        try:
            if self.verbose >= 3: print(f"{Fore.YELLOW}\tRemove file:{Fore.RESET} {fn}")
            os.remove(fp)
            time.sleep(.1)
        except OSError as e:
            print(f"{Fore.RED}\tError removing {fp}: {e}{Fore.RESET}")

    def replace_text(self, *args, root: str, files: list, repls: dict, **kwargs) -> None:
        """
        purpose: Replace text in each file under root according to repls (case-aware).
        """
        for fn in files:
            fp = os.path.join(root, fn)
            if not os.path.isfile(fp): continue
            try: self._apply_repls(fp=fp, repls=repls)
            except Exception as e:
                print(f"{Fore.RED}\tError processing file {fp}: {e}{Fore.RESET}")

    def _apply_repls(self, *args, fp: str, repls: dict, **kwargs) -> None:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            contents = f.read()
        new = contents
        for old, val in repls.items():
            if val is not None: new = self._case_repl(text=new, old=old, new=val)
        if new != contents:
            with open(fp, 'w', encoding='utf-8') as f: f.write(new)

    @staticmethod
    def _case_repl(*args, text: str, old: str, new: str, **kwargs) -> str:
        text = text.replace(old, new)
        if old.islower():
            text = text.replace(old.capitalize(), new.capitalize())
        return text.replace(old.upper(), new.upper())

    def remove_marked_lines(self, *args, root: str, files: list, **kwargs) -> None:
        """
        purpose: Strip lines containing the REMOVE_MARKER from each file under root.
        """
        for fn in files:
            fp = os.path.join(root, fn)
            if not os.path.isfile(fp): continue
            if self._strip_marked(fp=fp) and self.verbose >= 3:
                print(f"{Fore.GREEN}\tRemoved lines in:{Fore.RESET} {fn}")

    def _strip_marked(self, *args, fp: str, **kwargs) -> bool:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            contents = f.read()
        if self.REMOVE_MARKER not in contents: return False
        kept = [ln for ln in contents.splitlines() if self.REMOVE_MARKER not in ln]
        with open(fp, 'w', encoding='utf-8') as f: f.write('\n'.join(kept))
        return True
