"""
script_path: src/protolib/core/apis/info.py
purpose: >-
  Gather and display information about the Python environment, project structure,
  and package details.
description: |-
  Outputs are collected via collect_infos() and rendered in
  a single pass. Lines marked with clone_remove_line are stripped during cloning
  so that protolib-specific content does not bleed into derived packages.
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""

import fnmatch, os, sys
try:
    import pyperclip as _pyperclip
    _has_pyperclip = True
except ImportError:
    _has_pyperclip = False
from tabulate import tabulate as tb
from colorama import Fore, Style

import protolib.core.settings as sts
from protolib.helpers.tree import Tree
from protolib.helpers.import_info import main as import_info
# from protopy.helpers.package_info import pipenv_is_active

from protolib.core.creator.clone import clone_info
import protolib.helpers.printing as printing
from protolib.helpers.printing import logprint, Color, MODULE_COLORS
MODULE_COLORS["info"] = Color.MAGENTA

all_infos = {"python", "package"}
_INFO_LIST: list = []

def collect_infos(msg: str, *args, init=False, **kwargs) -> list:
    if init: _INFO_LIST.clear()
    if msg: _INFO_LIST.append(str(msg))
    return _INFO_LIST


_HINT_MSG = (
    f"{Fore.YELLOW}\nfor more infos: {Style.RESET_ALL}proto info "
    f"{Fore.YELLOW}-i{Style.RESET_ALL} {all_infos} "
    f"{Fore.YELLOW}-v{Style.RESET_ALL} [1, 2, 3, 5, 7, 99]"
)

def _dispatch_infos(*args, verbose, infos: set, **kwargs):
    for info in infos:
        try:
            getattr(sys.modules[__name__], f"{info}_info")(*args, verbose=verbose, **kwargs)
        except Exception as e:
            print(f"{Fore.RED}ERROR:{Fore.RESET} in {info}_info {e = }. Skipping...")

def get_infos(*args, verbose, infos: set = None, **kwargs):
    collect_infos('', True)
    if infos:
        _dispatch_infos(*args, verbose=verbose, infos=infos, **kwargs)
    collect_infos(_HINT_MSG)
    cloning_info(*args, verbose=verbose, **kwargs)
    user_info(*args, **kwargs)
    server_info(*args, **kwargs)

def cloning_info(*args, verbose: int = 0, **kwargs):
    collect_infos(f"\n{Fore.YELLOW}{f' CLONE INFO ':-^80}{Fore.RESET} ")
    collect_infos(clone_info(*args, **kwargs))

def user_info(*args, **kwargs):
    msg = f"\n{f' {sts.package_name.upper()} USER info ':#^80}"
    collect_infos(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")

def server_info(*args, **kwargs):
    msg = f"{Fore.YELLOW}Modify User settings{Fore.RESET}: {sts.user_settings_path}!\n"
    collect_infos(msg)
    msg = (f"{Fore.YELLOW}serve:{Fore.RESET} proto server "
           f"{Style.DIM}# port is {sts.port}{Style.RESET_ALL}\n")
    collect_infos(msg)

def python_info(*args, **kwargs):
    collect_infos(f"""\n{Fore.YELLOW}{f" PYTHON info ":#^80}{Style.RESET_ALL}""")
    collect_infos(f"{sys.executable = }\n{sys.version}\n{sys.version_info}")
    with open(os.path.join(sts.project_dir, "pyproject.toml"), "r") as f:
        collect_infos(f.read())

def _pkg_header(*args, **kwargs):
    collect_infos(f"""\n{Fore.YELLOW}{f" PACKAGE info ":#^80}{Style.RESET_ALL}""")
    collect_infos(f"\n{sts.project_name = }\n{sts.package_dir = }\n{sts.test_dir = }")
    collect_infos(f"\n\n{sts.project_dir = }")
    collect_infos(f"{sts.package_name = }\n")
    collect_infos(f"$PWD: {os.getcwd()}\n$EXE: {sys.executable}"
                  f" -> {venv_is_active(sys.executable) = }\n")

def _pkg_tree(*args, verbose: int = 0, **kwargs):
    tree = Tree(*args, verbose=verbose, **kwargs)(
        sts.project_dir, colorized=True, ignores=sts.ignore_dirs, verbose=verbose)
    collect_infos(f"{tree.get('tree')}\n")
    if verbose:
        collect_infos(f"{tree.get('contents')}\n")

def _pkg_imports_readme(*args, **kwargs):
    src = import_info(main_file_name='protopy.py', verbose=0)
    collect_infos(f"Project import structure:\n{src}")
    with open(os.path.join(sts.project_dir, "Readme.md"), "r") as f:
        collect_infos(f"\n<readme>\n{f.read()}\n</readme>\n")

def package_info(*args, verbose: int = 0, **kwargs):
    _pkg_header(*args, **kwargs)
    _pkg_tree(*args, verbose=verbose, **kwargs)
    _pkg_imports_readme(*args, **kwargs)


# project environment info
def venv_is_active(exec_path, *args, **kwargs):
    """
    purpose: Check if the uv venv is active.
    description: uv places the venv at <project_dir>/.venv, so we check for '.venv' in
      the path.
    """
    return '.venv' in exec_path.replace('\\', '/')

def _clip_output(*args, out: str, **kwargs):
    if _has_pyperclip:
        _pyperclip.copy(out)
        print(f"{Fore.GREEN}Copied to clipboard!{Style.RESET_ALL}")
    else:
        msg = "pyperclip not installed — clipboard copy skipped."
        print(f"{Fore.YELLOW}{msg}{Style.RESET_ALL}")

def main(*args, clip=None, verbose: int = 0, **kwargs) -> str:
    get_infos(*args, verbose=verbose, **kwargs)
    out = "\n".join(collect_infos(f""))
    print(out)
    if clip: _clip_output(*args, out=out, **kwargs)
    if verbose >= 2: printing.pretty_dict('main.kwargs', kwargs)
    return out

if __name__ == "__main__":
    main(verbose=2, infos=all_infos, clip=False)