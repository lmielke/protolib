# info.py
import subprocess
import os, sys, time
import requests
from tabulate import tabulate as tb

import protopy.settings as sts
from protopy.helpers.collections import group_text
from protopy.helpers.sys_info.dirs_info import Tree
from protopy.helpers.sys_info.os_info import get_os_info
from protopy.helpers.application_logger.application_info import ApplicationInfo
from protopy.helpers.sys_info.user_info import Userhistory
from protopy.helpers.sys_info.import_info import main as import_info
import protopy.helpers.sys_info.git_diff as git_diff
from protopy.helpers.sys_info.package_info import pipenv_is_active, pipenv_info

from protopy.helpers.sys_state import state_cache

all_infos = {"git_diff", "os", "network", "python", "package", "project", "docker", "os_activity", "ps_history"}
info_list = []

def collect_infos(msg:str, *args, init:bool=None, **kwargs):
    global info_list
    if init is not None:
        info_list.clear()
    else: 
        cleaned = str(msg).replace('\\', '/').replace('//', '/')
        info_list.append(cleaned)
    return info_list

def get_infos(*args, verbose, infos: set = None, **kwargs):
    if verbose >= 2 or  ("package" in infos):
        package_info(*args, **kwargs)
    if verbose >= 2 or ("project" in infos):
        project_info(*args, infos=infos, **kwargs)
    if verbose >= 2 or ("os" in infos):
        system_info(*args, **kwargs)
    if verbose >= 3 or ("network" in infos):
        network_info(*args, **kwargs)
    if verbose >= 2 or ("python" in infos):
        python_info(*args, **kwargs)
    if verbose >= 3 or ("docker" in infos):
        collect_infos(docker_info(*args, **kwargs))
    if verbose >= 3 or ("git_diff" in infos):
        collect_infos(git_diff.main(    *args,
                                        startDir=sts.project_dir, 
                                        days=1, 
                                        projectName='protolib',
                                        verbose=0,
                                        **kwargs,
                    )
        )
    if verbose >= 1 or ("os_activity" in infos):
        collect_infos(f"""\n{sts.YELLOW}{f" proto info -i os_activity ":#^60}{sts.ST_RESET}""")
        file_name, log = ApplicationInfo.load_log_file('today', *args, **kwargs)
        cnt, logs = 0, []
        for k, vs in log.items():
            logs.append(f"{k}:\n{vs}")
            cnt += 1
            if cnt > 5: break
        collect_infos('\n\n'.join(logs))
    if verbose >= 1 or ("ps_history" in infos):
        text_len = 30
        collect_infos(f"""\n{sts.YELLOW}{f" proto info -i ps_history ":#^60}{sts.ST_RESET}""")
        collect_infos([h for h in Userhistory().get_ps_history(text_len, *args, **kwargs) \
                                                                if not 'proto info' in h])
    if verbose or ("user_info" in infos):
        user_info(*args, **kwargs)

def user_info(*args, **kwargs):
    msg = f"""\n{f" PROTOPY USER info ":#^60}"""
    msg += (
        f"{sts.YELLOW}\nfor more infos:{sts.ST_RESET}\n"
        f"proto info -i {' '.join(all_infos)} or -v 1-3"
        )
    collect_infos(f"{sts.GREEN}{msg}{sts.ST_RESET}")
    # how to cone info
    from protopy.creator.clone import clone_info

    collect_infos(clone_info(*args, **kwargs))

def package_info(*args, regex:str=sts.package_name, **kwargs):
    """
    This displays the import structure of the package starting at file_name.
    """
    collect_infos(f"""\n{sts.YELLOW}{f" proto info -i PACKAGE ":#^60}{sts.ST_RESET}""")
    collect_infos("Here are some infos about our relevant python package.")
    ignores = sts.ignore_dirs | {'gp', 'models'}
    collect_infos(f"{Tree(coloreds=None,).mk_tree(sts.project_dir, ignores=ignores,)}\n")
    file_name = regex if regex is not None else sts.package_name
    if not file_name.endswith('.py'):
        file_name += '.py'
    collect_infos( f"{import_info(main_file_name=file_name, verbose=0, )}" )
    collect_infos(f"{sts.package_name = }\n")
    collect_infos(pipenv_info())
    collect_infos(
                    (
                        f"$PWD: {os.getcwd()}\n"
                        f"$EXE: {sys.executable} -> {pipenv_is_active(sys.executable) = }\n"
                        )
        )

def project_info(*args, api:str=None, verbose:int=0, show:str=False, infos:list=None, **kwargs):
    collect_infos(f"""\n{sts.YELLOW}{f" proto info -i PROJECT ":#^60}{sts.ST_RESET}""")
    collect_infos("Here are some general project infos.")
    pr_infos = [f"{sts.project_name = }", f"{sts.package_dir = }", f"{sts.test_dir = }"]
    collect_infos('\n'.join(pr_infos))
    collect_infos(f"\n\n{sts.project_dir = }")
    ignores = sts.ignore_dirs | {'gp', 'models'}
    if not 'package' in infos:
        collect_infos(f"{Tree(coloreds=None,).mk_tree(sts.project_dir, ignores=ignores,)}\n")
    # turns out, that visualizing a file structure using graphviz is not the best idea
    # if show:
    #     tree.view_graph(sts.project_dir, render_format='png', view=True)
    collect_infos(
                    subprocess.run(f"proto -h".split(), text=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                    ).stdout
    )
    collect_infos( f"Project import structure:\n"
                   f"{import_info(main_file_name='protopy.py', verbose=0, )}" )
    # collect_infos( f"{regex}:\n{import_info(main_file_name=file_name, **kwargs)}" )
    with open(os.path.join(sts.project_dir, "Readme.md"), "r") as f:
        collect_infos(f"\n<readme>\n{f.read()}\n</readme>\n")
        # package help

def system_info(*args, **kwargs):
    collect_infos(f"""\n{sts.YELLOW}{f" proto info -i OS ":#^60}{sts.ST_RESET}""")
    collect_infos("Here are some infos about the underlying operating os.")
    sys_info = {k: group_text(v, 50) for k, v in get_os_info().items()}
    collect_infos(sys_info)
    # collect_infos(tb(sys_info.items(), headers="keys", tablefmt="psql", showindex=True))

def network_info(*args, **kwargs):
    collect_infos(f"""\n{sts.YELLOW}{f" proto info -i NETWORK ":#^60}{sts.ST_RESET}""")
    # get external ip_adress and other relevant network info
    cmd = "ipconfig" if sys.platform == "win32" else "ifconfig"
    output = subprocess.check_output(cmd).decode()
    ip_adress = [line.split(":")[1].strip() for line in output.split("\n") if "IPv4" in line]
    collect_infos(f"{ip_adress = }")
    collect_infos(f"{requests.get('https://api.ipify.org').text = }")


def python_info(*args, **kwargs):
    collect_infos(f"""\n{sts.YELLOW}{f" proto info -i PYTHON ":#^60}{sts.ST_RESET}""")
    collect_infos("Here are some infos about the installed python.")
    py_infos = [f"{sys.executable = }", f"{sys.version = }", f"{sys.version_info = }"]
    collect_infos('\n'.join( py_infos ))


@state_cache(max_cache_hours=1)
def docker_info(*args, **kwargs):
    docker_tbl = f"""\n{sts.YELLOW}{f" proto info -i DOCKER ":#^60}{sts.ST_RESET}\n"""
    try:
        # some docker infos now
        cmd = "docker info" if sys.platform == "win32" else "docker info"
        output = subprocess.check_output(cmd).decode()
        d_infos = {
            line.split(":")[0].strip(): line.split(":")[1].strip()
            for line in output.split("\n")
            if ":" in line
        }
        d_infos = {k: group_text(v.strip(), 70) for k, v in d_infos.items()}
        docker_tbl += tb(d_infos.items(), headers="keys", tablefmt="psql", showindex=True)
    except Exception as e:
        docker_tbl += f"{sts.RED}Docker not running! {e = }\n{sts.ST_RESET}"
    return docker_tbl

def get_file_info(*args, tgt_dir:str, infos:list=None, **kwargs):
    # mk_tree finds the file matches to be displayed
    tree, manifest = Tree(coloreds=tgt_dir,), []
    dir_tree = tree.mk_tree(sts.project_dir, ignores=sts.ignore_dirs, )
    collect_infos(f"\n<files>\n")
    for file_path in tree.matches:
        pf = file_path.replace(sts.project_dir, 'sts.project_dir').replace(os.sep, '/')
        manifest.append(pf)
        with open(file_path, 'r') as f:
            content = '\n'.join([f"{i:<3}: {l}" for i, l in enumerate(f.read().split('\n'), 1)])
            collect_infos(  f"{sts.DIM}{pf}{sts.ST_RESET}\n"
                            f"```{sts.file_types.get(os.path.splitext(file_path)[1])}\n"
                            f"{content}```\n"
            )
    file_manifest = '\n- '.join(manifest)
    collect_infos(
                    f"## Attached files manifest, "
                    f"selection regex: r'{tree.coloreds}':\n- {file_manifest}\n"
    )
    collect_infos(f"</files>")

def run(*args, tgt_dir:str=None, infos:list=None, verbose:int=0, **kwargs):
    infos = set() if infos is None else {i.lower() for i in infos}
    collect_infos('', *args, **kwargs)
    if tgt_dir:
        get_file_info(*args, tgt_dir=tgt_dir, infos=infos, verbose=verbose, **kwargs)
        infos.add('package')
    if infos or verbose:
        get_infos(*args, infos=infos, verbose=verbose, **kwargs)
    return '\n'.join(collect_infos(f''))

def main(owner:str=None, *args, yes=False, init=True, infos:list=None, **kwargs):
    collect_infos('', *args, init=True, **kwargs)
    out = run(*args, infos=infos, **kwargs)
    if yes:
        with open(os.path.join(sts.test_data_dir, 'test_text.txt'), 'w', encoding='utf-8') as f:
            f.write(out)
    return out