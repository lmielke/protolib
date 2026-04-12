# clone.py
import protolib.settings as sts
from protolib.helpers.printing import logprint, Color, MODULE_COLORS
MODULE_COLORS["clone"] = Color.MAGENTA
from colorama import Fore, Style
import subprocess
import os, re, shutil, stat, sys, time
from typing import List, Dict, Tuple

# needed for cloning - aliased to avoid confusion with this script's own main()
from protolib.creator.archive import main as archive_main

DEFAULT_PORT = 9001
project_params = {
    "pr_name": "protolib",
    "pg_name": "protopy",
    "alias": "proto",
    "port": str(DEFAULT_PORT),
}


path_patterns = {
    'file_patterns': [r'.*\.log$', r'.*\.lock$', r'.*\.tmp$', r'^temp.*', r'^clone\.py$'],
}

# --- fast python version discovery (cross-platform) --------------------------
_VER_RX = re.compile(r"Python\s+(\d+\.\d+\.\d+)")
_IS_WIN = sys.platform == "win32"

def _run(*args, cmd: list[str], **kwargs) -> str:
    try: return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    except Exception: return ""

def _from_py_launcher(*args, **kwargs) -> set[str]:
    """Windows: py launcher."""
    if not _IS_WIN: return set()
    out = _run(cmd=["py", "-0p"])
    return {ln.split(": ", 1)[-1] for ln in out.splitlines() if ": " in ln}

def _from_pyenv(*args, **kwargs) -> set[str]:
    """pyenv-win (Windows) and pyenv (Linux/Mac)."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".pyenv", "pyenv-win", "versions"),  # Windows
        os.path.join(home, ".pyenv", "versions"),                # Linux/Mac
    ]
    exes = set()
    exe_name = "python.exe" if _IS_WIN else "python3"
    for root in candidates:
        if not os.path.isdir(root): continue
        for d in os.listdir(root):
            p = os.path.join(root, d, "bin", exe_name) if not _IS_WIN else os.path.join(root, d, exe_name)
            if os.path.exists(p): exes.add(p)
    return exes

def _from_uv(*args, **kwargs) -> set[str]:
    """uv-managed Python installs."""
    uv_root = os.path.join(os.path.expanduser("~"), ".local", "share", "uv", "python")
    if not os.path.isdir(uv_root): return set()
    exes = set()
    exe_name = "python.exe" if _IS_WIN else "python3"
    for d in os.listdir(uv_root):
        p = os.path.join(uv_root, d, "bin", exe_name)
        if os.path.exists(p): exes.add(p)
    return exes

def _from_path(*args, **kwargs) -> set[str]:
    """Scan PATH for python executables."""
    sep = ";" if _IS_WIN else ":"
    names = ([f"python{s}.exe" for s in ("", "3", "3.11", "3.12", "3.13")] if _IS_WIN
             else [f"python{s}" for s in ("3", "3.11", "3.12", "3.13", "3.14")])
    out = set()
    for p in os.environ.get("PATH", "").split(sep):
        if not p or not os.path.exists(p): continue
        for n in names:
            exe = os.path.join(p, n)
            if os.path.exists(exe): out.add(os.path.abspath(exe))
    return out

def _version_of(*args, exe: str, **kwargs) -> str | None:
    m = _VER_RX.search(_run(cmd=[exe, "--version"]))
    return m.group(1) if m else None

def get_installed_py_versions(*args, **kwargs) -> list[str]:
    """Returns unique X.Y and X.Y.Z version strings detected on this host."""
    exes = set().union(_from_py_launcher(), _from_pyenv(), _from_uv(), _from_path())
    vers = set()
    for e in exes:
        v = _version_of(exe=e)
        if not v: continue
        mm = ".".join(v.split(".")[:2])
        vers.add(v); vers.add(mm)
    def _k(s: str): return tuple(int(x) for x in s.split("."))
    return sorted(vers, key=_k)

def clone_info(*args, **kwargs):
    """
    Helps user to understand how to use clone.py and which parameters to use.
    """
    full_versions = sorted({
        v for v in get_installed_py_versions() if len(v.split(".")) == 3
    }, key=lambda s: tuple(map(int, s.split("."))))
    example = next((v for v in reversed(full_versions) if v.count(".") == 2), None)
    short = ".".join(example.split(".")[:2]) if example else "3.11"
    shown = ", ".join(full_versions)

    msg = (
        f"{Fore.YELLOW}NOTE, to Clone the package use:{Fore.RESET}\n\n"
        f"\tproto clone "
        f"{Fore.YELLOW}-pr{Fore.RESET} 'badylib' "
        f"{Fore.YELLOW}-n{Fore.RESET} 'badypackage' "
        f"{Fore.YELLOW}-a{Fore.RESET} 'bady' "
        f"{Fore.YELLOW}-t{Fore.RESET} '/tmp' "
        f"{Fore.YELLOW}-p{Fore.RESET} '{example}' "
        f"{Fore.YELLOW}--port{Fore.RESET} 9006 "
        f"{Fore.YELLOW}--install\n\n"
        f"Parameter Explained: \n"
        f"\t{Fore.CYAN}Mandatory:{Fore.RESET} \n"
        f"\t{Fore.YELLOW}-pr{Fore.RESET} [name of target project], \n"
        f"\t{Fore.YELLOW}-n{Fore.RESET} [package name used inside project],  \n"
        f"\t{Fore.YELLOW}-a{Fore.RESET} [package alias],  \n"
        f"\t{Fore.YELLOW}-t{Fore.RESET} [target directory],  \n"
        f"\t{Fore.YELLOW}--port{Fore.RESET} [HTTP port for server.py]\n"
        f"\t{Fore.CYAN}Optionals:{Fore.RESET} \n"
        f"\t{Fore.YELLOW}-p{Fore.RESET} [Python version for env]  \n"
        f"\t{Fore.YELLOW}--install{Fore.RESET} [run uv sync]\n"
        f"\t{Fore.YELLOW}-y{Fore.RESET} [skip confirmation prompts]\n"
        f"\nAvailable Python versions: {Fore.CYAN}{shown}{Fore.RESET}\n"
        f"{Fore.YELLOW}Note:{Fore.RESET} You can also use short versions like "
        f"{Fore.CYAN}{short}{Fore.RESET} if they map to a valid patch (e.g. {example})."
    )
    return msg


def set_python_version_in_pyproject(pyproject_path: str, *args, py_version: str = None,
                                     verbose: int = 0, **kwargs) -> None:
    """
    Set requires-python in pyproject.toml to the given version.

    :param pyproject_path: Path to pyproject.toml.
    :param py_version: Python version string e.g. '3.13' or '3.13.1'.
    """
    if py_version is None:
        if verbose >= 2:
            print(f"{Fore.YELLOW}\tSkipping pyproject.toml Python version update: py_version not provided.{Fore.RESET}")
        return

    short_version = ".".join(py_version.split(".")[:2])
    try:
        with open(pyproject_path, 'r') as f:
            lines = f.readlines()
        with open(pyproject_path, 'w') as f:
            found = False
            for line in lines:
                if line.strip().startswith('requires-python'):
                    f.write(f'requires-python = ">={short_version}"\n')
                    found = True
                else:
                    f.write(line)
            if not found:
                print(f"{Fore.YELLOW}\tWarning: 'requires-python' not found in {pyproject_path}.{Fore.RESET}")
    except FileNotFoundError:
        print(f"{Fore.RED}\tError: pyproject.toml not found at {pyproject_path}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}\tError updating {pyproject_path}: {e}{Fore.RESET}")


def rename_files(root: str, file_names: List[str], file_rules: Dict[str, str],
                 *args, verbose: int = 0, **kwargs) -> None:
    """
    Rename files according to specified rules.

    :param root: The root directory containing the files.
    :param file_names: List of filenames within the root directory.
    :param file_rules: Dictionary with old_name:new_name renaming pairs.
    """
    for file_name in file_names:
        for old_name, new_name in file_rules.items():
            if new_name is None: continue
            file, ext = os.path.splitext(file_name)
            if old_name in file:
                repl_name = file_name.replace(old_name, new_name)
                old_path = os.path.join(root, file_name)
                new_path = os.path.join(root, repl_name)
                if os.path.exists(old_path) and old_path != new_path:
                    if verbose >= 3:
                        print(f"\t{Fore.BLUE}Rename file:{Fore.RESET} {old_path} to {new_path}")
                    os.rename(old_path, new_path)
                break

def rename_dirs(root: str, dirs: List[str], file_rules: Dict[str, str],
                *args, verbose: int = 0, **kwargs) -> None:
    """
    Rename directories according to specified rules.

    :param root: The root directory containing the subdirectories.
    :param dirs: List of subdirectory names within the root directory.
    :param file_rules: Dictionary with old_name:new_name renaming pairs.
    """
    renamed_dirs_this_pass = set()
    for dir_name in list(dirs):
        for old_name, new_name in file_rules.items():
            if new_name is None: continue
            if dir_name == old_name and old_name not in renamed_dirs_this_pass:
                old_path = os.path.join(root, old_name)
                new_path = os.path.join(root, new_name)
                if os.path.exists(old_path) and old_path != new_path:
                    if verbose >= 3:
                        print(f"{Fore.BLUE}\tRename directory:{Fore.RESET} {old_path} to {new_path}")
                    os.rename(old_path, new_path)
                    renamed_dirs_this_pass.add(new_name)
                break


def remove_files(root: str, file_names: List[str], file_patterns: List[str],
                 *args, verbose: int = 0, **kwargs) -> None:
    """
    Remove files that match given file_patterns within a specific root directory.
    """
    for filename in file_names:
        file_path = os.path.join(root, filename)
        if any(re.match(pattern, filename) for pattern in file_patterns):
            if os.path.exists(file_path):
                try:
                    if verbose >= 3:
                        print(f"{Fore.YELLOW}\tRemove file:{Fore.RESET} {filename}")
                    os.remove(file_path)
                    time.sleep(.1)
                except OSError as e:
                    print(f"{Fore.RED}\tError removing file {file_path}: {e}{Fore.RESET}")


def initalize(*args, tgt_dir: str = None, new_pr_name: str = None,
              new_pg_name: str = None, new_alias: str = None,
              yes: bool = False, verbose: int = 0, **kwargs) -> Tuple[str, str, str, str]:
    """
    Initialize and confirm user inputs for the project setup.
    """
    if tgt_dir is None:
        tgt_dir = input(f"{Fore.YELLOW}Enter target directory "
                        f"for your project (e.g., /path/to/parent_dir): {Fore.RESET}").strip()
    tgt_dir = os.path.expanduser(tgt_dir)

    if new_pg_name is None:
        new_pg_name = input(f"{Fore.YELLOW}Enter new package name (e.g., mypackage): {Fore.RESET}").strip()

    if (new_pr_name is None or new_pr_name == new_pg_name) and not yes:
        prompt_message = (
            f"\n{Fore.YELLOW}READ THIS:{Fore.RESET} "
            f"\nYour Python package (importable name) will be '{Fore.YELLOW}{new_pg_name}{Fore.RESET}'. "
            f"The project directory (folder on disk containing your package and other files like setup.py) "
            f"is currently set to be named '{Fore.YELLOW}{new_pr_name}{Fore.RESET}'."
            f"\nIf you want a different project directory name (recommended if it's same as package name), "
            f"enter it now. Otherwise, press Enter to keep it as '{new_pr_name}'.\n"
            f"Enter new project directory name: "
        )
        user_pr_name = input(prompt_message).strip()
        if user_pr_name:
            new_pr_name = user_pr_name
        elif new_pr_name is None:
            new_pr_name = new_pg_name
            if verbose >= 2:
                print(f"{Fore.CYAN}Project directory name will be '{new_pr_name}'.{Fore.RESET}")


    if new_alias is None:
        if verbose >= 2:
            print(f"{Fore.CYAN}No alias provided; alias-based replacements might be skipped.{Fore.RESET}")


    new_pr_dir_path = os.path.abspath(os.path.join(tgt_dir, new_pr_name))

    confirmation_message = (
        f"\n{Fore.CYAN}Project will be created with these names:{Fore.RESET}"
        f"\n  Project Directory: {Fore.YELLOW}{new_pr_dir_path}{Fore.RESET}"
        f"\n  Package Name:      {Fore.YELLOW}{new_pg_name}{Fore.RESET}"
        f"\n  Alias (if used):   {Fore.YELLOW}{new_alias or 'N/A'}{Fore.RESET}"
        f"\nContinue? [Y/n] (default is Y): "
    )

    if not yes:
        if input(confirmation_message).strip().lower() == "n":
            print(f"{Fore.RED}Operation canceled by user.{Fore.RESET}")
            sys.exit()

    if 'protolib' in new_pr_dir_path and 'protolib' not in os.path.abspath(sts.project_dir):
        print(f"{Fore.RED}Safety check: Target directory appears to be related to 'protolib' itself in an unexpected way.")
        print(f"Target: {new_pr_dir_path}{Fore.RESET}")
        print(f"To avoid accidental data loss, please choose a different target directory or project name.")
        sys.exit()

    return os.path.abspath(tgt_dir), new_pr_name, new_pg_name, new_alias


def copy_project(src_dir: str, *args, tgt_dir: str = None, new_pr_name: str = None,
                 verbose: int = 0, **kwargs) -> None:
    """Copies the project using archive_main."""
    if verbose >= 1:
        print(f"{Fore.CYAN}Copying project from '{src_dir}' to '{tgt_dir}' and renaming to '{new_pr_name}'...{Fore.RESET}")
    archive_main(**{
        'sources': [src_dir],
        'target': [tgt_dir],
        'rename': new_pr_name,
        'comment': 'protolib initializer',
        'allYes': True,
        'direct': 1,
        'verbose': 0,
    })
    if verbose >= 1:
        print(f"{Fore.GREEN}Project copied successfully.{Fore.RESET}")

def copy_resources(*args, tgt_dir: str = None, new_pr_name: str = None,
                   pg_name: str = 'protolib', verbose: int = 0, **kwargs) -> None:
    """
    from tgt_dir/new_pr_name/src/pg_name/resources copy arguments.py and settings.py
    into the new package directory tgt_dir/new_pr_name/src/pg_name.
    """
    pg_dir = os.path.join(tgt_dir, new_pr_name, "src", pg_name)
    resources_dir = os.path.join(pg_dir, "resources")
    if not os.path.exists(resources_dir):
        print(f"{Fore.YELLOW}Resources directory {resources_dir} does not exist. Skipping resource copy.{Fore.RESET}")
        return
    if verbose >= 2:
        print(f"Found:{Fore.YELLOW}{os.listdir(pg_dir)}{Fore.RESET}")

    for file_name in ["arguments.py", "settings.py", "Readme.md", "protolib.service"]:
        src_file_path = os.path.join(resources_dir, file_name)
        if file_name in ('Readme.md', 'protolib.service'):
            tgt_file_path = os.path.join(tgt_dir, new_pr_name, file_name)
        else:
            tgt_file_path = os.path.join(tgt_dir, new_pr_name, "src", pg_name, file_name)

        if os.path.exists(src_file_path):
            shutil.copy2(src_file_path, tgt_file_path)
            if verbose >= 2:
                print(f"{Fore.GREEN}Copied {file_name} to {tgt_file_path}{Fore.RESET}")
        else:
            if verbose >= 2:
                print(f"{Fore.YELLOW}Resource file {src_file_path} does not exist. Skipping copy.{Fore.RESET}")
    try:
        shutil.rmtree(resources_dir)
        if verbose >= 2:
            print(f"{Fore.GREEN}Removed resources directory: {resources_dir}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}Error removing resources directory {resources_dir}: {e}{Fore.RESET}")


def replace_text_in_files(root: str, file_names: List[str], text_repls: Dict[str, str],
                          *args, verbose: int = 0, **kwargs) -> None:
    """
    Replace specific text patterns in files with new text.
    """
    for file_name in file_names:
        file_path = os.path.join(root, file_name)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    file_contents = file.read()

                new_contents = file_contents
                for old_text, new_text in text_repls.items():
                    if new_text is None: continue

                    new_contents = new_contents.replace(old_text, new_text)
                    if old_text.islower():
                        new_contents = new_contents.replace(old_text.capitalize(), new_text.capitalize())
                    new_contents = new_contents.replace(old_text.upper(), new_text.upper())

                if new_contents != file_contents:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(new_contents)
                    if verbose >= 3:
                        print(f"{Fore.GREEN}\tUpdated text in:{Fore.RESET} {file_name}")
            except Exception as e:
                print(f"{Fore.RED}\tError processing file {file_path}: {e}{Fore.RESET}")

def remove_lines_in_files(root: str, file_names: List[str], *args,
                          verbose: int = 0, **kwargs) -> None:
    marker = '# clone_remove_line'
    for file_name in file_names:
        file_path = os.path.join(root, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                file_contents = file.read()
            if marker in file_contents:
                new_contents, removed_lines = [], []
                for line in file_contents.splitlines():
                    if marker in line:
                        removed_lines.append(line)
                    else:
                        new_contents.append(line)
                new_contents = '\n'.join(new_contents)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_contents)
                if verbose >= 3:
                    print(  f"{Fore.GREEN}\tRemoved lines in:{Fore.RESET} {file_name}\n"
                            f"{removed_lines = }")

def setup_project(n_pr_dir: str, *args, new_pg_name: str = None, py_version: str = None,
                  install: bool = False, verbose: int = 0, **kwargs) -> None:
    """Builds and optionally installs the new project using uv."""
    if not install:
        if verbose >= 1:
            print(f"{Fore.GREEN}\nSkipping install. Run 'uv sync' in '{n_pr_dir}' to set up the environment.{Fore.RESET}")
        return

    if verbose >= 1:
        print(f"{Fore.CYAN}\nInstalling project environment using uv...{Fore.RESET}")
    uv_bin = os.path.join(os.path.expanduser("~"), ".local", "bin", "uv")
    uv_cmd = [uv_bin if os.path.exists(uv_bin) else "uv", "sync"]
    if py_version:
        uv_cmd += ["--python", py_version]

    if verbose >= 1:
        print(f"{Fore.YELLOW}Now running:{Fore.RESET} {' '.join(uv_cmd)} in {n_pr_dir}")
    try:
        subprocess.check_call(uv_cmd, cwd=n_pr_dir)
        if verbose >= 1:
            print(f"{Fore.GREEN}\nDONE! Environment for '{new_pg_name}' set up.{Fore.RESET}")
            print(f"To activate: source {n_pr_dir}/.venv/bin/activate")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}uv sync failed: {e}{Fore.RESET}")
    except FileNotFoundError:
        print(f"{Fore.RED}'uv' not found. Install it from https://docs.astral.sh/uv/{Fore.RESET}")


def manage_replacements(old_params: Dict[str, str], new_params: Dict[str, str],
                        *args, **kwargs) -> Dict[str, str]:
    """
    Create a dictionary for text replacements based on old and new project parameters.
    """
    text_repls = {}
    for key in old_params:
        old_val = old_params.get(key)
        new_val = new_params.get(key)

        if old_val and new_val is not None:
            text_repls[old_val] = new_val
            if old_val.islower() and old_val.isalpha():
                 text_repls[old_val.capitalize()] = new_val.capitalize()
                 text_repls[old_val.upper()] = new_val.upper()
            elif not old_val.islower() and not old_val.isupper():
                 text_repls[old_val.upper()] = new_val.upper()
    return text_repls


def clone_and_install(*args, verbose: int = 0, **kwargs):
    """
    Main function to handle the renaming and removal of files and directories
    based on new project parameters.
    """
    tgt_dir, new_pr_name, new_pg_name, new_alias = initalize(
        *args, verbose=verbose, **kwargs
    )
    # Push potentially modified values back into kwargs so downstream
    # functions can pull them from their signature defaults.
    kwargs.update(tgt_dir=tgt_dir, new_pr_name=new_pr_name,
                  new_pg_name=new_pg_name, new_alias=new_alias)

    new_project_path = os.path.join(tgt_dir, new_pr_name)
    if verbose >= 1:
        print(f"\n{Fore.CYAN}Initialization complete. Project details:{Fore.RESET}")
        print(f"  Target Directory (parent): {tgt_dir}")
        print(f"  New Project Directory Name: {new_pr_name}")
        print(f"  New Package Name: {new_pg_name}")
        print(f"  New Alias: {new_alias or 'N/A'}")
        print(f"  Full Project Path: {new_project_path}")

    new_params_for_replacement = {
        "pr_name": new_pr_name,
        "pg_name": new_pg_name,
        "alias": new_alias,
        "port": str(kwargs.get('port')),
    }
    text_replacements = manage_replacements(project_params, new_params_for_replacement,
                                           *args, **kwargs)

    file_renaming_rules = {}
    if project_params.get("pr_name") and new_pr_name:
        file_renaming_rules[project_params["pr_name"]] = new_pr_name
    if project_params.get("pg_name") and new_pg_name:
        file_renaming_rules[project_params["pg_name"]] = new_pg_name
    if project_params.get("alias") and new_alias:
        file_renaming_rules[project_params["alias"]] = new_alias

    copy_project(sts.project_dir, *args, verbose=verbose, **kwargs)
    copy_resources(*args, verbose=verbose, **kwargs)

    if verbose >= 1:
        print(f"\n{Fore.BLUE}Starting restructuring in: {new_project_path}{Fore.RESET}")

    for root, dirs, files in os.walk(new_project_path, topdown=False):
        dirs[:] = [d for d in dirs if d not in sts.ignore_dirs]
        if verbose >= 3:
            print(f"Processing directory: {root}")
        remove_files(root, files, path_patterns['file_patterns'],
                     *args, verbose=verbose, **kwargs)
        rename_files(root, files, file_renaming_rules,
                     *args, verbose=verbose, **kwargs)
        rename_dirs(root, dirs, file_renaming_rules,
                    *args, verbose=verbose, **kwargs)

    if verbose >= 1:
        print(f"\n{Fore.BLUE}Replacing text content...{Fore.RESET}")
    for root, dirs, files in os.walk(new_project_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in sts.ignore_dirs]
        replace_text_in_files(root, files, text_replacements,
                              *args, verbose=verbose, **kwargs)
        remove_lines_in_files(root, files, *args, verbose=verbose, **kwargs)

    pyproject_full_path = os.path.join(new_project_path, 'pyproject.toml')
    set_python_version_in_pyproject(
        pyproject_full_path,
        *args, verbose=verbose, **kwargs
    )

    if verbose >= 2:
        print(f"\n{Fore.CYAN}Debug Info:{Fore.RESET} Project Path='{new_project_path}', Package Name='{new_pg_name}'")

    setup_project(
        new_project_path,
        *args,
        verbose=verbose,
        **kwargs
    )
    return new_project_path

def run_checks(*args, install: bool = False, py_version: str = None,
               port: str | int = None, verbose: int = 0, **kwargs) -> None:
    """Checks python version format and required port."""
    if verbose >= 2:
        print(f"{Fore.CYAN}Running pre-checks: install={install}, "
              f"py_version='{py_version or 'Not set'}', port='{port}'{Fore.RESET}")

    if port is None:
        print(f"{Fore.RED}Error: --port is required (e.g., --port 9006).{Fore.RESET}")
        sys.exit()
    try:
        port_i = int(port)
        if not (1 <= port_i <= 65535):
            raise ValueError
    except Exception:
        print(f"{Fore.RED}Error: invalid --port '{port}'. Use 1..65535.{Fore.RESET}")
        sys.exit()

    if install and py_version is None:
        print(f"{Fore.RED}Error: Python version (-p) must be specified when using the "
              f"install flag.{Fore.RESET}")
        sys.exit()

    if py_version is None: return
    if not re.match(r'^\d+\.\d+(\.\d+)?$', py_version):
        print((f"{Fore.RED}Error: Invalid Python version for -p: '{py_version}'. "
               f"Expected '3.11' or '3.11.4'.{Fore.RESET}"))
        sys.exit()

    available = set(get_installed_py_versions())
    if py_version not in available:
        mm = ".".join(py_version.split(".")[:2])
        if mm not in available:
            print(f"{Fore.RED}Error: Python '{py_version}' not found on this system."
                  f"{Fore.RESET}")
            print(f"{Fore.YELLOW}Available: "
                  f"{', '.join(get_installed_py_versions())}{Fore.RESET}")
            sys.exit()

def main(*args, api: str = None, verbose: int = 0, **kwargs) -> str:
    """
    Calling wrapper for the clone operation.
    """
    run_checks(*args, verbose=verbose, **kwargs)
    logprint(f"cloning kwargs: {kwargs}", level='warning', console_log=False)
    print(f"\n{Fore.CYAN}Starting clone with parameters:{Fore.RESET}")
    print(f"  Project: {Fore.YELLOW}{kwargs.get('new_pr_name', 'N/A')}{Fore.RESET}")
    print(f"  Package: {Fore.YELLOW}{kwargs.get('new_pg_name', 'N/A')}{Fore.RESET}")
    print(f"  Alias:   {Fore.YELLOW}{kwargs.get('new_alias', 'N/A')}{Fore.RESET}")
    print(f"  Target:  {Fore.YELLOW}{kwargs.get('tgt_dir', 'N/A')}{Fore.RESET}")
    print(f"  Port:    {Fore.YELLOW}{kwargs.get('port', 'N/A')}{Fore.RESET}")
    new_project_path = clone_and_install(*args, verbose=verbose, **kwargs)
    print(f"\n{Fore.GREEN}Cloning completed successfully!{Fore.RESET}")
    print(
        f"\n{Fore.YELLOW}Now read {Fore.CYAN}{new_project_path}/Readme.md{Fore.RESET}"
        f"{Fore.YELLOW} and follow the instructions.{Fore.RESET}"
    )
    return "Clone successful"
