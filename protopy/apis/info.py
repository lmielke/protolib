# info.py
import subprocess
import os, sys
import requests
from tabulate import tabulate as tb
from colorama import Fore, Style

import protopy.settings as sts
from protopy.protopy import ExampleClass
from protopy.helpers.tree import Tree
from protopy.helpers.import_info import main as import_info
from protopy.helpers.package_info import pipenv_is_active

all_infos = {"python", "package"}


def collect_infos(msg:str, info_list:list=[]):
    info_list.append(str(msg))
    return info_list

def get_infos(*args, verbose, infos: set = set(), **kwargs):
    if infos:
        for info in infos:
            try:
                getattr(sys.modules[__name__], f"{info}_info")(*args, verbose=verbose, **kwargs)
            except AttributeError:
                print(f"{Fore.YELLOW}Warning:{Fore.RESET} {info}_info function not found. Skipping...")
    collect_infos(
                    f"{Fore.YELLOW}\nfor more infos: "
                    f"{Style.RESET_ALL}proto info -i {all_infos} or -v 1-3"
            )
    user_info(*args, **kwargs)

def user_info(*args, **kwargs):
    msg = f"""\n{f" PROTOPY USER info ":#^80}"""
    collect_infos(f"{Fore.GREEN}{msg}{Style.RESET_ALL}")
    # how to clone infos                         # clone_remove_line
    from protopy.creator.clone import clone_info # clone_remove_line
    collect_infos(clone_info(*args, **kwargs))   # clone_remove_line

def python_info(*args, **kwargs):
    collect_infos(f"""\n{Fore.YELLOW}{f" PYTHON info ":#^80}{Style.RESET_ALL}""")
    collect_infos(f"{sys.executable = }\n{sys.version}\n{sys.version_info}")
    with open(os.path.join(sts.project_dir, "Pipfile"), "r") as f:
        collect_infos(f.read())


def package_info(*args, verbose:int=0, **kwargs):
    collect_infos(f"""\n{Fore.YELLOW}{f" PROJECT info ":#^80}{Style.RESET_ALL}""")
    collect_infos(f"\n{sts.project_name = }\n{sts.package_dir = }\n{sts.test_dir = }")
    collect_infos(f"\n\n{sts.project_dir = }")
    collect_infos(f"{sts.package_name = }\n")
    collect_infos(
                    (
                        f"$PWD: {os.getcwd()}\n"
                        f"$EXE: {sys.executable} -> {pipenv_is_active(sys.executable) = }\n"
                        )
        )
    ignores = sts.ignore_dirs | {'gp', 'models'}
    collect_infos(f"{Tree().mk_tree(sts.project_dir, colorized=True, ignores=ignores)}\n")
    try:
        collect_infos(
                    subprocess.run(f"bady -h".split(), text=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                    ).stdout
        )
    except Exception as e:
        print(f"{Fore.RED}Error:{Fore.RESET} {e}")
    collect_infos( f"Project import structure:\n"
                   f"{import_info(main_file_name='protopy.py', verbose=0, )}" )
    with open(os.path.join(sts.project_dir, "Readme.md"), "r") as f:
        collect_infos(f"\n<readme>\n{f.read()}\n</readme>\n")
        # package help

def main(*args, **kwargs):
    get_infos(*args, **kwargs)
    out = '\n'.join(collect_infos(f'info.main({kwargs})'))
    # print(f'info.main({kwargs})')
    # sys.stdout.write(f'info.main({kwargs})')
    return out