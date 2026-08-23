"""
script_path: src/protolib/core/apis/info.py
description: >-
  Gathers and displays information about the Python environment, project structure, and package
  details. The InfoCollector class owns the accumulator list and all info-gathering methods,
  while module-level wrappers delegate to a singleton instance. Lines marked with clone_remove_line
  are stripped during cloning to prevent protolib-specific content from bleeding into derived
  packages.
tags:
- cli
- info
- parsing
"""

import os, sys
try:
    import pyperclip as _pyperclip
    _has_pyperclip = True
except ImportError:
    _has_pyperclip = False
from colorama import Fore, Style

import protolib.core.settings as sts
from protolib.helpers.tree import Tree
from protolib.helpers.import_info import main as import_info

from protolib.core.creator.clone import clone_info
from protolib.helpers.printing import Color, MODULE_COLORS
MODULE_COLORS["info"] = Color.MAGENTA

all_infos = {"python", "package"}

_HINT_MSG = (
    f"{Fore.YELLOW}\nfor more infos: {Style.RESET_ALL}proto info "
    f"{Fore.YELLOW}-i{Style.RESET_ALL} {all_infos} "
    f"{Fore.YELLOW}-v{Style.RESET_ALL} [1, 2, 3, 5, 7, 99]"
)


class InfoCollector:
    """
    description: Owns the accumulator list so info gathering is free of module-level
      mutable state. All section methods append to self._info_list; main() renders it.
    """

    def __init__(self, *args, **kwargs):
        self._info_list: list = []

    # ------------------------------------------------------------------ accumulator

    def collect(self, msg: str, *args, init: bool = False, **kwargs) -> list:
        """description: Append msg to the list; init=True resets first."""
        if init: self._info_list.clear()
        if msg: self._info_list.append(str(msg))
        return self._info_list

    # ------------------------------------------------------------------ sections

    def _dispatch_infos(self, *args, infos: set = None, **kwargs):
        """description: Call <info>_info() for each name in infos."""
        if not infos:
            return
        for info in infos:
            try:
                getattr(self, f"{info}_info")(*args, **kwargs)
            except Exception as e:
                print(f"{Fore.RED}ERROR:{Fore.RESET} in {info}_info {e = }. Skipping...")

    def get_infos(self, *args, **kwargs):
        """description: Reset accumulator, dispatch named sections, append footer."""
        self.collect('', *args, init=True, **kwargs)
        self._dispatch_infos(*args, **kwargs)
        self.collect(_HINT_MSG, *args, **kwargs)
        self.cloning_info(*args, **kwargs)
        self.user_info(*args, **kwargs)
        self.server_info(*args, **kwargs)

    def cloning_info(self, *args, **kwargs):
        """description: Append clone section."""
        self.collect(f"\n{Fore.YELLOW}{f' CLONE INFO ':-^80}{Fore.RESET} ", *args, **kwargs)
        self.collect(clone_info(*args, **kwargs), *args, **kwargs)

    def user_info(self, *args, **kwargs):
        """description: Append user section header."""
        msg = f"\n{f' {sts.package_name.upper()} USER info ':#^80}"
        self.collect(f"{Fore.GREEN}{msg}{Style.RESET_ALL}", *args, **kwargs)

    def server_info(self, *args, **kwargs):
        """description: Append server / settings hints."""
        self.collect(
            f"{Fore.YELLOW}Modify User settings{Fore.RESET}: {sts.user_settings_path}!\n",
            *args, **kwargs)
        self.collect(
            f"{Fore.YELLOW}serve:{Fore.RESET} proto server "
            f"{Style.DIM}# port is {sts.port}{Style.RESET_ALL}\n",
            *args, **kwargs)

    def python_info(self, *args, **kwargs):
        """description: Append Python environment section."""
        self.collect(f"\n{Fore.YELLOW}{f' PYTHON info ':#^80}{Style.RESET_ALL}", *args, **kwargs)
        self.collect(f"{sys.executable = }\n{sys.version}\n{sys.version_info}", *args, **kwargs)
        with open(os.path.join(sts.project_dir, "pyproject.toml"), "r") as f:
            self.collect(f.read(), *args, **kwargs)

    def _pkg_header(self, *args, **kwargs):
        self.collect(f"\n{Fore.YELLOW}{f' PACKAGE info ':#^80}{Style.RESET_ALL}", *args, **kwargs)
        self.collect(f"\n{sts.project_name = }\n{sts.package_dir = }\n{sts.test_dir = }", *args, **kwargs)
        self.collect(f"\n\n{sts.project_dir = }", *args, **kwargs)
        self.collect(f"{sts.package_name = }\n", *args, **kwargs)
        self.collect(
            f"$PWD: {os.getcwd()}\n$EXE: {sys.executable}"
            f" -> {venv_is_active(sys.executable, *args, **kwargs) = }\n",
            *args, **kwargs)

    def _pkg_tree(self, *args, verbose: int = 0, **kwargs):
        tree = Tree(*args, **kwargs)(
            sts.project_dir, colorized=True, ignores=sts.ignore_dirs, verbose=verbose)
        self.collect(f"{tree.get('tree')}\n", *args, **kwargs)
        if verbose:
            self.collect(f"{tree.get('contents')}\n", *args, **kwargs)

    def _pkg_imports_readme(self, *args, **kwargs):
        src = import_info(*args, main_file_name='protopy.py', **kwargs)
        self.collect(f"Project import structure:\n{src}", *args, **kwargs)
        with open(os.path.join(sts.project_dir, "Readme.md"), "r") as f:
            self.collect(f"\n<readme>\n{f.read()}\n</readme>\n", *args, **kwargs)

    def package_info(self, *args, **kwargs):
        """description: Append full package info section."""
        self._pkg_header(*args, **kwargs)
        self._pkg_tree(*args, **kwargs)
        self._pkg_imports_readme(*args, **kwargs)

    # ------------------------------------------------------------------ output

    def main(self, *args, clip: bool = None, **kwargs) -> str:
        """description: Collect all infos, print, optionally copy to clipboard."""
        self.get_infos(*args, **kwargs)
        out = "\n".join(self.collect('', *args, **kwargs))
        print(out)
        if clip:
            _clip_output(*args, out=out, **kwargs)
        return out


# ------------------------------------------------------------------ module singleton + wrappers

_collector = InfoCollector()

def collect_infos(msg: str, *args, init: bool = False, **kwargs) -> list:
    """description: Module-level wrapper — delegates to _collector.collect()."""
    return _collector.collect(msg, *args, init=init, **kwargs)

def get_infos(*args, **kwargs):
    """description: Module-level wrapper — delegates to _collector.get_infos()."""
    return _collector.get_infos(*args, **kwargs)

def cloning_info(*args, **kwargs):
    """description: Module-level wrapper — delegates to _collector.cloning_info()."""
    return _collector.cloning_info(*args, **kwargs)

def user_info(*args, **kwargs):
    """description: Module-level wrapper — delegates to _collector.user_info()."""
    return _collector.user_info(*args, **kwargs)

def server_info(*args, **kwargs):
    """description: Module-level wrapper — delegates to _collector.server_info()."""
    return _collector.server_info(*args, **kwargs)

def python_info(*args, **kwargs):
    """description: Module-level wrapper — delegates to _collector.python_info()."""
    return _collector.python_info(*args, **kwargs)

def package_info(*args, **kwargs):
    """description: Module-level wrapper — delegates to _collector.package_info()."""
    return _collector.package_info(*args, **kwargs)

def main(*args, clip: bool = None, **kwargs) -> str:
    """description: Module-level wrapper — delegates to _collector.main()."""
    return _collector.main(*args, clip=clip, **kwargs)


# ------------------------------------------------------------------ pure utilities

def venv_is_active(exec_path, *args, **kwargs) -> bool:
    """
    description: uv places the venv at <project_dir>/.venv, so we check for '.venv' in
      the path.
    """
    return '.venv' in exec_path.replace('\\', '/')

def _clip_output(*args, out: str, **kwargs):
    """description: Copy output to clipboard if pyperclip is available."""
    if _has_pyperclip:
        _pyperclip.copy(out)
        print(f"{Fore.GREEN}Copied to clipboard!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}pyperclip not installed — clipboard copy skipped.{Style.RESET_ALL}")


if __name__ == "__main__":
    main(verbose=2, infos=all_infos, clip=False)