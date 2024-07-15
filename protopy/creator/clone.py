# clone.py
import protopy.settings as sts
import subprocess
import os, re, shutil, stat, sys, time
from typing import List, Dict, Tuple

project_params = {
                    "project_name": "protolib", 
                    "pg_name": "protopy", 
                    "alias": "proto", }

path_patterns = {
            'file_patterns': [r'.*\.log$', r'.*\.lock$', r'.*\.tmp$', r'^temp.*', r'^clone\.py$'],
            }

def clone_info(*args, **kwargs):
    """
    Helps user to understand how to use clone.py and which paramets to use for cloning
    proto clone -pr 'badylib' -n 'badypack' -a 'bady' -t '/temp' -p 3.11
    """
    msg = (
            f"\n{sts.YELLOW}CLONE INFO:{sts.RESET} "
            f"to clone protopy use proto clone like this:\n"
            f"proto clone "
            f"{sts.YELLOW}-pr{sts.RESET} 'badylib' "
            f"{sts.YELLOW}-n{sts.RESET} 'badypackage' "
            f"{sts.YELLOW}-a{sts.RESET} 'bady' "
            f"{sts.YELLOW}-t{sts.RESET} '/temp' "
            f"{sts.YELLOW}-p{sts.RESET} '3.11'\n"
            f"where: {sts.YELLOW}-pr{sts.RESET} [name of project directory], "
            f"{sts.YELLOW}-n{sts.RESET} [package name], {sts.YELLOW}-a{sts.RESET} [alias] "
            f"{sts.YELLOW}-t{sts.RESET} [target directory], {sts.YELLOW}-p{sts.RESET} [python version]\n"
            )
    return msg


def set_python_version_in_pipfile(pipfile_path: str, *args, py_version: str, **kwargs) -> None:
    """
    Set the specified Python version in the Pipfile.
    
    :param pipfile_path: Path to the Pipfile where the Python version is to be set.
    :param py_version: The Python version to set in the Pipfile.
    """
    with open(pipfile_path, 'r') as file:
        lines = file.readlines()
    # python version has to be changed to desired python
    with open(pipfile_path, 'w') as file:
        for line in lines:
            if line.startswith('python_version'):
                file.write(f'python_version = "{py_version}"\n')
            else:
                file.write(line)

def rename_files(root: str, file_names: List[str], file_rules: Dict[str, str]) -> None:
    """
    Rename files according to specified rules.
    
    :param root: The root directory containing the files.
    :param file_names: List of filenames within the root directory.
    :param file_rules: Dictionary with old_name:new_name renaming pairs.
    """
    for file_name in file_names:
        for old_name, new_name in file_rules.items():
            file, ext = os.path.splitext(file_name)
            if old_name in file:
                repl_name = file_name.replace(old_name, new_name)
                old_path = os.path.join(root, file_name)
                new_path = os.path.join(root, repl_name)
                if os.path.exists(old_path):
                    print(f"\t{sts.BLUE}Rename file:{sts.RESET} {old_path} to {new_path}")
                    os.rename(old_path, new_path)
                break

def rename_dirs(root: str, dirs: List[str], file_rules: Dict[str, str]) -> None:
    """
    Rename directories according to specified rules.
    
    :param root: The root directory containing the subdirectories.
    :param dirs: List of subdirectory names within the root directory.
    :param file_rules: Dictionary with old_name:new_name renaming pairs.
    """
    renamed_dirs = set()
    for dir_name in dirs:
        for old_name, new_name in file_rules.items():
            if dir_name == old_name and old_name not in renamed_dirs:
                old_path = os.path.join(root, old_name)
                new_path = os.path.join(root, new_name)
                if os.path.exists(old_path):
                    print(f"{sts.BLUE}\tRename directory:{sts.RESET} {old_path} to {new_path}")
                    os.rename(old_path, new_path)
                    renamed_dirs.add(old_name)
                break

def remove_files(root: str, file_names: List[str], file_patterns: List[str]) -> None:
    """
    Remove files that match given file_patterns within a specific root directory.
    
    This function iterates over a list of file_names. For each filename, it constructs the full path
    and checks if the filename matches any of the specified file_patterns. If it does, the file is removed.
    
    :param root: The root directory containing the files.
    :param file_names: List of file_names within the root directory.
    :param file_patterns: List of string file_patterns to match for file removal.
    """
    for filename in file_names:
        file_path = os.path.join(root, filename)
        if any(re.match(pattern, filename) for pattern in file_patterns):
            if os.path.exists(file_path):
                print(f"{sts.YELLOW}\tRemove file:{sts.RESET} {filename}")
                os.remove(file_path)
                time.sleep(.1)

def initalize(tgt_dir: str, new_pr_name: str, new_pg_name: str, new_alias: str, yes: bool = False, **kwargs)\
                                                             -> Tuple[str, str, str, str]:
    """
    Initialize and confirm user inputs for the project setup.
    
    :param tgt_dir: Target directory for the project.
    :param new_pr_name: New project name.
    :param new_pg_name: New package name.
    :param new_alias: New alias for the package.
    :return: Tuple containing the confirmed target directory, project name, package name, and alias.
    """
    if tgt_dir is None:
        tgt_dir = input(f"{sts.YELLOW}Enter tgt dir for your package, tgt_dir: {sts.RESET}")
    tgt_dir = os.path.dirname(tgt_dir) if tgt_dir.endswith(new_pg_name) else tgt_dir
    if new_pg_name is None:
        new_pg_name = input(f"{sts.YELLOW}Enter new package name, new_pg_name: {sts.RESET}")
    if new_pr_name is None or new_pr_name == new_pg_name:
        msg = (
            f"\n{sts.YELLOW}READ THIS:{sts.RESET} "
            f"\nYour package will be named {sts.YELLOW}{new_pg_name}{sts.RESET}. "
            f"The package parent directory name is: {sts.YELLOW}{new_pr_name}{sts.RESET}."
            f"\nEnter a valid name of your package dir "
            f"{sts.YELLOW}(different from {new_pg_name}){sts.RESET}, new_pr_name: "
        )
        new_pr_name = input(msg)
    new_pr_dir = os.path.abspath(os.path.join(tgt_dir, new_pr_name))
    # confirm and go
    msg = (
            f"\nContinue renaming all files in {sts.RED}{new_pr_dir}{sts.RESET} ?"
            f" [y/n] default is [n] : "
            )
    if not yes:
        if input(msg).upper() != "Y":
            print(f"{sts.RED}Operation canceled by user.{sts.RESET}")
            exit()
    if 'protopy' in new_pr_dir:
        print(f"{sts.RED}You cannot change protopy files: {new_pr_dir}{sts.RESET}")
        exit()
    return os.path.abspath(tgt_dir), new_pr_name, new_pg_name, new_alias

def copy_project(src_dir: str, tgt_dir:str, new_pr_name:str) -> str:
    from protopy.creator.archive import main
    main(**{
            'sources': [src_dir], 
            'target': [tgt_dir], 
            'rename': new_pr_name, 
            'comment': 'protopy initializer', 
            'allYes': False, 
            'direct': 1, 
            'verbose': 0
            }
        )

def replace_text_in_files(root: str, file_names: List[str], text_repls: Dict[str, str]) -> None:
    """
    Replace specific text patterns in files with new text. This includes direct,
    capitalized, and uppercase matches of the old text.
    
    :param root: The root directory containing the files.
    :param file_names: List of filenames within the root directory to be processed.
    :param text_repls: Dictionary with old_text:new_text replacement pairs.
    """
    for file_name in file_names:
        file_path = os.path.join(root, file_name)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as file:
                    file_contents = file.read()
                # check and replace
                new_contents = file_contents
                for old_text, new_text in text_repls.items():
                    # Replace direct hit
                    new_contents = new_contents.replace(old_text, new_text)
                    # Replace capitalized version
                    new_contents = new_contents.replace(old_text.capitalize(), new_text.capitalize())
                    # Replace uppercase version
                    new_contents = new_contents.replace(old_text.upper(), new_text.upper())
                # overwrite file
                if new_contents != file_contents:
                    with open(file_path, 'w') as file:
                        file.write(new_contents)
                    print(f"{sts.GREEN}\tUpdated text in:{sts.RESET} {file_name}")
            except UnicodeDecodeError as e:
                pass

def setup_project(n_pr_dir, n_pg_name, *args, py_version:str, install:bool=False, **kwargs):
    setupStr = f"python {n_pr_dir}/setup.py sdist"
    with open(os.path.join(n_pr_dir, "setup.cfg"), "r") as f:
        text = f.read()
        version = re.search(r"version = (.*)", text).group(1)
    print(f"{sts.YELLOW}\nNow running:{sts.RESET} {setupStr} in {n_pr_dir}")
    subprocess.call(setupStr.split(), shell=True, cwd=n_pr_dir)
    # list tar.gz
    tarthing = f"tar --list -f {n_pr_dir}/dist/{n_pg_name}-{version}.tar.gz"
    print(f"{sts.YELLOW}\nNow running:{sts.RESET} {tarthing} in {n_pr_dir}")
    subprocess.call(tarthing.split(), shell=True, cwd=n_pr_dir)
    # script stopps here if -install flag was not provided
    print(f"{sts.YELLOW}\n\n--{bool(install) = } {sts.RESET}")
    if not install: return
    # install environment
    installer = f"pipenv install --dev --python {py_version}"
    subprocess.call(installer.split(), shell=True, cwd=n_pr_dir)
    # test installation
    cmds = "pipenv", "run", "python", "-m", "unittest"
    print(f"{sts.YELLOW}\nDONE ! - TESTING IN 3secs:{sts.RESET} {cmds} in {n_pr_dir}")
    time.sleep(3)
    # subprocess.call(cmds, shell=True, cwd=n_pr_dir)

def manage_replacements(old_params: Dict[str, str], new_params: Dict[str, str]) -> Dict[str, str]:
    """
    Create a dictionary for text replacements based on old and new project parameters.
    
    :param old_params: Dictionary with old parameter names and values.
    :param new_params: Dictionary with new parameter names and values.
    :return: Dictionary with text replacements.
    """
    text_repls = {old: new for old, new in zip(old_params.values(), new_params.values())\
                                                                     if new is not None}
    # Add capitalized and uppercased variants
    additional_replacements = {
        old.upper(): new.upper() for old, new in text_repls.items()
    }
    additional_replacements.update({
        old.capitalize(): new.capitalize() for old, new in text_repls.items()
    })
    text_repls.update(additional_replacements)
    return text_repls

def clone_and_install(*args, **kwargs):
    """
    Main function to handle the renaming and removal of files and directories
    based on new project parameters.
    
    :param new_pr_name: New project name.
    :param new_pg_name: New package name.
    :param new_alias: New alias.
    """
    # Create rename rules based on project parameters and additional patterns
    tgt_dir, new_pr_name, new_pg_name, new_alias = initalize(*args, **kwargs)
    new_pr_dir = os.path.join(tgt_dir, new_pr_name)
    print('params: ', tgt_dir, new_pr_name, new_pg_name, new_alias)
    pr_params = {"project_name": "protolib", "pg_name": "protopy", "alias": "proto"}
    new_pr_params = {
                        "new_pr_name": new_pr_name, 
                        "new_pg_name": new_pg_name, 
                        "new_alias": new_alias
                        }
    text_repls = manage_replacements(pr_params, new_pr_params)
    file_rules = {
                        project_params["project_name"]: new_pr_name,
                        project_params["pg_name"]: new_pg_name,
                        project_params["alias"]: new_alias,
                        # Add additional manual patterns here if needed
    }
    copy_project(sts.project_dir, tgt_dir, new_pr_name)
    # Iterate over directories and files using os.walk
    print(f"\n{sts.BLUE}Starting restructuring:{sts.RESET}")
    for root, dirs, files in os.walk(new_pr_dir, topdown=False):
        # Remove files and directories
        print(f"Directory: {root}:")
        remove_files(root, files, path_patterns['file_patterns'])
        # Rename files and directories
        rename_files(root, files, file_rules)
        rename_dirs(root, dirs, file_rules)
    for root, dirs, files in os.walk(new_pr_dir, topdown=False):
        replace_text_in_files(root, files, text_repls)
    set_python_version_in_pipfile(os.path.join(new_pr_dir, 'Pipfile'), *args, **kwargs)
    print(f"{new_pr_dir = }, {new_pg_name = }, {args = }, {kwargs = }")
    # setup_project(new_pr_dir, new_pg_name, *args, install=kwargs['install'])
    setup_project(new_pr_dir, new_pg_name, *args, **kwargs)

def run_checks(*args, install:bool, py_version:str, **kwargs) -> None:
    if install:
        print(f"{sts.BLUE}run_checks.install.py_version: {py_version}{sts.RESET}")
        if py_version is None:
            print(f"{sts.RED}You must specify python version to install with -p {sts.RESET}")
            exit()
    if py_version is not None:
        print(f"{sts.BLUE}run_checks.not None.py_version: {py_version}{sts.RESET}")
        if not re.match(r'^\d+\.\d+$', py_version):
            print((
                    f"{sts.RED}You must provide a valid python version for -p {sts.RESET}"
                    f"{sts.RED}\npy_version: {py_version}{sts.RESET}"
                    ))
            exit()

def main(*args, api:str=None, **kwargs) -> None:
    run_checks(*args, **kwargs)
    clone_and_install(*args, **kwargs)
    print(f"{sts.GREEN}Exiting! {sts.RESET}")
    return f"install successful!"
