"""
script_path: src/protolib/core/creator/clone.py
description: >-
  Orchestrates the cloning of the protolib template into a new project by collecting inputs,
  copying the tree, and transforming files. Builds text-replacement and rename rules from
  old to new identity mappings. Validates user-supplied port and Python version before execution.
  Consumed by the CLI entry point to generate a new project instance.
tags:
- cli
- infra
- staging
"""
import importlib, os, re, shutil, subprocess, sys
from colorama import Fore

import protolib.core.settings as sts
from protolib.core.creator.python_versions import PythonVersions
from protolib.core.creator.clones import Clones
from protolib.core.creator.gate import run_gate
from protolib.core.creator.tree_transform import TreeTransformer
from protolib.helpers.printing import Color, MODULE_COLORS

MODULE_COLORS["clone"] = Color.MAGENTA
DEFAULT_PORT = 9001


class CloneParams:
    """
    description: Builds text-replacement and rename rules.
    """

    KEYS = ("pr_name", "pg_name", "alias", "port")

    def __init__(self, *args, old: dict, new: dict, **kwargs):
        self.old = self._norm(*args, mapping=old, **kwargs)
        self.new = self._norm(*args, mapping=new, **kwargs)

    @staticmethod
    def _norm(*args, mapping: dict, **kwargs) -> dict:
        out = dict(mapping)
        if out.get("port") is not None: out["port"] = str(out["port"])
        return out

    @classmethod
    def from_settings(cls, source_settings, *args, new_pr_name, new_pg_name,
                      new_alias=None, new_port=None, **kwargs):
        """
        description: Build params from source settings; new_* args specify the clone's identity.
        """
        old = {"pr_name": source_settings.project_name,
               "pg_name": source_settings.package_name,
               "alias": getattr(source_settings, "alias", "proto"),
               "port": getattr(source_settings, "port", DEFAULT_PORT)}
        new = {"pr_name": new_pr_name, "pg_name": new_pg_name,
               "alias": new_alias, "port": new_port}
        return cls(old=old, new=new)

    def text_repls(self, *args, **kwargs) -> dict:
        """
        description: Build text-replacement dict (with case variants) from old to new.
        """
        repls = {}
        for key in self.KEYS:
            old_val, new_val = self.old.get(key), self.new.get(key)
            if old_val and new_val is not None:
                self._add_case_variants(*args, repls=repls, old=old_val, new=new_val, **kwargs)
        return repls

    @staticmethod
    def _add_case_variants(*args, repls: dict, old: str, new: str, **kwargs) -> None:
        repls[old] = new
        if old.islower() and old.isalpha():
            repls[old.capitalize()] = new.capitalize()
            repls[old.upper()] = new.upper()
        elif not old.islower() and not old.isupper():
            repls[old.upper()] = new.upper()

    def file_rules(self, *args, **kwargs) -> dict:
        """
        description: Build file/dir rename rules from old to new (skipping None values).
        """
        keys = ("pr_name", "pg_name", "alias")
        return {self.old[k]: self.new[k] for k in keys
                if self.old.get(k) and self.new.get(k)}


class Validator:
    """
    description: Validates user-supplied port and python version before clone runs.
    """

    def __init__(self, *args, py_versions: PythonVersions = None, **kwargs):
        self.pv = py_versions or PythonVersions(*args, **kwargs)

    def check(self, *args, **kwargs):
        self._check_port(*args, **kwargs)
        self._check_py(*args, **kwargs)
        self._check_alias(*args, **kwargs)

    @staticmethod
    def _check_port(*args, port=None, **kwargs) -> None:
        if port is None: _exit_red("Error: --port is required (e.g., --port 9006).", *args, **kwargs)
        try:
            if not (1 <= int(port) <= 65535): raise ValueError
        except Exception: _exit_red(f"Error: invalid --port '{port}'. Use 1..65535.", *args, **kwargs)

    @staticmethod
    def _check_alias(*args, new_alias=None, **kwargs) -> None:
        if new_alias and len(new_alias) < 3:
            _exit_red(f"Error: --new_alias '{new_alias}' too short (need \u22653 chars).", *args, **kwargs)

    def _check_py(self, *args, **kwargs):
        self._check_py_format(*args, **kwargs)

    def _check_py_format(self, *args, py_version=None, install=False, **kwargs) -> None:
        if install and py_version is None:
            _exit_red("Error: Python version (-p) required with --install.", *args, **kwargs)
        if py_version is None: return
        if not re.match(r'^\d+\.\d+(\.\d+)?$', py_version):
            _exit_red(f"Error: Invalid Python version: '{py_version}'.", *args, **kwargs)
        avail = set(self.pv.all())
        mm = ".".join(py_version.split(".")[:2])
        if py_version not in avail and mm not in avail:
            _exit_red(f"Error: Python '{py_version}' not found.", *args, **kwargs)


class CloneUI:
    """
    description: 'Handles user interaction: input prompts, confirmation, safety check.'
    """

    def collect(self, *args, new_alias=None, yes=False, **kwargs):
        td, pg = self._collect_inputs(*args, **kwargs)
        kwargs.update({'new_pg_name': pg, 'new_alias': new_alias, 'yes': yes})
        pr = self._resolve_pr_name(*args, **kwargs)
        path = os.path.abspath(os.path.join(td, pr))
        if not yes: self._confirm_or_exit(*args, path=path, **kwargs)
        self._safety_check(*args, path=path, **kwargs)
        return os.path.abspath(td), pr, pg, new_alias

    def _resolve_pr_name(self, *args, **kwargs):
        return self._prompt_pr_name(*args, **kwargs)

    @staticmethod
    def _ask(question, *args, **kwargs) -> str:
        return input(f"{Fore.YELLOW}{question}: {Fore.RESET}").strip()

    @staticmethod
    def _collect_inputs(*args, tgt_dir=None, new_pg_name=None, **kwargs):
        if tgt_dir is None:
            tgt_dir = CloneUI._ask("Enter target dir (e.g., /path/to/parent_dir)")
        tgt_dir = os.path.expanduser(tgt_dir)
        if new_pg_name is None:
            new_pg_name = CloneUI._ask("Enter new package name (e.g., mypackage)")
        return tgt_dir, new_pg_name

    @staticmethod
    def _prompt_pr_name(*args, new_pr_name=None, new_pg_name=None, yes=False, **kwargs):
        if (new_pr_name is None or new_pr_name == new_pg_name) and not yes:
            prompt = (f"\n{Fore.YELLOW}READ THIS:{Fore.RESET}\nPackage: '{new_pg_name}', "
                      f"Project dir: '{new_pr_name}'."
                      "\nEnter new project directory name (or Enter to keep): ")
            user = input(prompt).strip()
            new_pr_name = user if user else new_pr_name
        return new_pr_name if new_pr_name is not None else new_pg_name

    @staticmethod
    def _confirm_or_exit(*args, path, new_pg_name, new_alias=None, **kwargs):
        msg = (f"\n{Fore.CYAN}Create project:{Fore.RESET}\n  Dir: {path}\n"
               f"  Pkg: {new_pg_name}\n  Alias: {new_alias or 'N/A'}\nContinue? [Y/n]: ")
        if input(msg).strip().lower() == "n": _exit_red("Canceled.", *args, **kwargs)

    @staticmethod
    def _safety_check(*args, path: str, **kwargs) -> None:
        if 'protolib' in path and 'protolib' not in os.path.abspath(sts.project_dir):
            _exit_red(f"Safety check: Target appears related to 'protolib'. Target: {path}", *args, **kwargs)

    @staticmethod
    def print_params(*args, new_pr_name=None, new_pg_name=None, new_alias=None,
                     tgt_dir=None, port=None, **kwargs) -> None:
        Y, R = Fore.YELLOW, Fore.RESET
        print(f"\n{Fore.CYAN}Starting clone with parameters:{R}")
        items = [("Project", new_pr_name), ("Package", new_pg_name),
                  ("Alias", new_alias), ("Target", tgt_dir), ("Port", port)]
        for label, val in items: print(f"  {label:8s}: {Y}{val or 'N/A'}{R}")

    @staticmethod
    def print_done(*args, path: str, **kwargs) -> None:
        print(f"\n{Fore.GREEN}Cloning completed!{Fore.RESET}")
        print(f"\n{Fore.YELLOW}Now read {Fore.CYAN}{path}/Readme.md"
              f"{Fore.RESET}{Fore.YELLOW} and follow the instructions.{Fore.RESET}")


class Cloner:
    """
    description: 'Orchestrates the full clone workflow: copy, transform, set version, install.'
    """

    def __init__(self, src_dir: str, *args, verbose: int = 0, source_settings=None, **kwargs):
        self.src_dir = src_dir
        self.verbose = verbose
        self.source_settings = source_settings or self._load_source_settings(*args, **kwargs)

    @staticmethod
    def _load_source_settings(*args, **kwargs):
        """description: Dynamically load the app-layer settings of the running package."""
        return importlib.import_module(f"{sts.package_name}.app.settings")

    def copy_project(self, tgt_dir: str, new_pr_name: str, *args, **kwargs) -> str:
        """
        description: Copy src_dir to tgt_dir/new_pr_name, skipping configured ignore_dirs.
        """
        dest = os.path.join(tgt_dir, new_pr_name)
        if self.verbose >= 1:
            print(f"{Fore.CYAN}Copying project from '{self.src_dir}'"
                  f" to '{dest}'...{Fore.RESET}")
        shutil.copytree(self.src_dir, dest, ignore=self._ignore, dirs_exist_ok=True)
        if self.verbose >= 1: print(f"{Fore.GREEN}Project copied successfully.{Fore.RESET}")
        return dest

    @staticmethod
    def _ignore(*args, **kwargs) -> set:
        """
        description: 'shutil.copytree ignore: skip ignore_dirs entries by basename.'
        """
        return {n for n in args[1] if n in sts.ignore_dirs}

    def transform(self, project_path, params, *args, py_version=None, **kwargs):
        tx = TreeTransformer(project_path, *args, ignore_dirs=sts.ignore_dirs, verbose=self.verbose, **kwargs)
        tx.restructure(params.file_rules())
        tx.rewrite(params.text_repls())
        tx.set_pyproject_version(os.path.join(project_path, 'pyproject.toml'), py_version)

    def setup(self, project_path, *args, install=False, **kwargs):
        if not install:
            self._skip_install(project_path, *args, **kwargs)
            return
        if self.verbose >= 1:
            print(f"{Fore.CYAN}\nInstalling project environment using uv...{Fore.RESET}")
        self._run_uv_sync(project_path, *args, **kwargs)

    def _skip_install(self, project_path, *args, **kwargs):
        if self.verbose < 1: return
        note = f"Skipping install. Run 'uv sync' in '{project_path}'."
        print(f"{Fore.GREEN}\n{note}{Fore.RESET}")

    def _run_uv_sync(self, project_path, *args, **kwargs) -> None:
        cmd = self._uv_cmd(*args, **kwargs)
        if self.verbose >= 1:
            print(f"{Fore.YELLOW}Now running:{Fore.RESET} {' '.join(cmd)} in {project_path}")
        self._exec_uv(cmd, project_path, *args, **kwargs)

    def _exec_uv(self, cmd, project_path, *args, **kwargs):
        try: subprocess.check_call(cmd, cwd=project_path)
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}uv sync failed: {e}{Fore.RESET}")
        except FileNotFoundError:
            print(f"{Fore.RED}'uv' not found. See https://docs.astral.sh/uv/{Fore.RESET}")

    @staticmethod
    def _uv_cmd(*args, py_version: str = None, **kwargs) -> list:
        uv_bin = os.path.join(os.path.expanduser("~"), ".local", "bin", "uv")
        cmd = [uv_bin if os.path.exists(uv_bin) else "uv", "sync"]
        if py_version: cmd += ["--python", py_version]
        return cmd

    def _post_gate(self, project_path: str, *args, install=False, **kwargs) -> None:
        """description: Run pytest inside the new clone. Skipped when --install is false."""
        if install: return run_gate(project_path, *args, **kwargs)
        if self.verbose >= 1: print(f"{Fore.YELLOW}Post-gate skipped.{Fore.RESET}")

    def run(self, *args, port=None, **kwargs):
        """description: Atomic clone workflow (collect, copy, transform, setup, gate)."""
        tgt_dir, pr_name, pg_name, alias = CloneUI().collect(**kwargs)
        params = CloneParams.from_settings(self.source_settings, new_pr_name=pr_name,
            new_pg_name=pg_name, new_alias=alias, new_port=port)
        project_path = self.copy_project(tgt_dir, pr_name, *args, **kwargs)
        self.transform(project_path, params, *args, **kwargs)
        self.setup(project_path, *args, **kwargs)
        self._post_gate(project_path, *args, **kwargs)
        return project_path

def _exit_red(msg: str, *args, **kwargs) -> None:
    print(f"{Fore.RED}{msg}{Fore.RESET}")
    sys.exit()

def clone_info(*args, **kwargs) -> str:
    """
    description: Return the formatted clone usage banner with installed Python versions.
    """
    return PythonVersions(*args, **kwargs).info_string()

def main(*args, port=None, py_version=None, install=False, verbose=0, **kwargs):
    """description: 'Entry point: validate, gate, print params, run clone, done.'"""
    Validator().check(port=port, py_version=py_version, install=install, **kwargs)
    run_gate(sts.project_dir, *args, **kwargs)
    CloneUI.print_params(port=port, **kwargs)
    cloner = Cloner(sts.project_dir, verbose=verbose)
    path = cloner.run(port=port, py_version=py_version, install=install, **kwargs)
    Clones(*args, **kwargs).add(path)
    CloneUI.print_done(path=path)
    return "Clone successful"

if __name__ == "__main__":
    main()
