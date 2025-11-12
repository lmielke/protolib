# clone.py
import protopy.settings as sts
from colorama import Fore, Style
import subprocess
import os, re, shutil, stat, sys, time
from typing import List, Dict, Tuple

# needed for cloning - aliased to avoid confusion with this script's own main()
from protopy.creator.archive import main as archive_main

DEFAULT_PORT = 9001
project_params = {
    "pr_name": "protolib",
    "pg_name": "protopy",
    "alias": "proto",
    "port": str(DEFAULT_PORT),  # <- add this
}


path_patterns = {
    'file_patterns': [r'.*\.log$', r'.*\.lock$', r'.*\.tmp$', r'^temp.*', r'^clone\.py$'],
}

# --- fast python version discovery (py, pyenv-win, PATH) ---------------------
_VER_RX = re.compile(r"Python\s+(\d+\.\d+\.\d+)")

def _run(*args, cmd: list[str], **kwargs) -> str:
    try: return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    except Exception: return ""

def _from_py_launcher(*args, **kwargs) -> set[str]:
    out = _run(cmd=["py", "-0p"])
    return {ln.split(": ", 1)[-1] for ln in out.splitlines() if ": " in ln}

def _from_pyenv(*args, **kwargs) -> set[str]:
    root = os.path.join(os.path.expanduser("~"), ".pyenv", "pyenv-win", "versions")
    if not os.path.isdir(root): return set()
    exes = set()
    for d in os.listdir(root):
        p = os.path.join(root, d, "python.exe")
        if os.path.exists(p): exes.add(p)
    return exes

def _from_path(*args, **kwargs) -> set[str]:
    names = [f"python{s}.exe" for s in ("", "3", "3.11", "3.12", "3.13")]
    out = set()
    for p in os.environ.get("PATH", "").split(";"):
        if not p or not os.path.exists(p): continue
        for n in names:
            exe = os.path.join(p, n)
            if os.path.exists(exe): out.add(os.path.abspath(exe))
    return out

def _version_of(*args, exe: str, **kwargs) -> str | None:
    m = _VER_RX.search(_run(cmd=[exe, "--version"]))
    return m.group(1) if m else None

def get_installed_py_versions(*args, **kwargs) -> list[str]:
    """
    WHY: Fast & robust. Returns unique X.Y and X.Y.Z strings detected on this host.
    """
    exes = set().union(_from_py_launcher(), _from_pyenv(), _from_path())
    vers = set()
    for e in exes:
        v = _version_of(exe=e)
        if not v: continue
        mm = ".".join(v.split(".")[:2])
        vers.add(v); vers.add(mm)
    # numeric sort for "3.9" < "3.10" < "3.11.9"
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
        f"{Fore.YELLOW}-t{Fore.RESET} '/temp' "
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
        f"\t{Fore.YELLOW}--install{Fore.RESET} [run pipenv install]\n"
        f"\nAvailable Python versions: {Fore.CYAN}{shown}{Fore.RESET}\n"
        f"{Fore.YELLOW}Note:{Fore.RESET} You can also use short versions like "
        f"{Fore.CYAN}{short}{Fore.RESET} if they map to a valid patch (e.g. {example})."
    )
    return msg


def set_python_version_in_pipfile(pipfile_path: str, *args, py_version: str = None, **kwargs) -> None:
    """
    Set the specified Python version in the Pipfile.

    :param pipfile_path: Path to the Pipfile where the Python version is to be set.
    :param py_version: The Python version to set in the Pipfile. Defaults to None.
    """
    if py_version is None:
        print(f"{Fore.YELLOW}\tSkipping Pipfile Python version update: py_version not provided.{Fore.RESET}")
        return

    try:
        with open(pipfile_path, 'r') as file:
            lines = file.readlines()
        
        with open(pipfile_path, 'w') as file:
            found_version_line = False
            for line in lines:
                if line.strip().startswith('python_version'):
                    file.write(f'python_version = "{py_version}"\n')
                    found_version_line = True
                else:
                    file.write(line)
            if not found_version_line: # If python_version was not in [requires]
                # This part might need adjustment based on Pipfile structure
                # Assuming it should be under a [requires] section if not present
                # For simplicity, we'll just print a warning if not found.
                # A more robust solution might involve parsing the TOML.
                print(f"{Fore.YELLOW}\tWarning: 'python_version' line not found in Pipfile {pipfile_path}. Version not set.{Fore.RESET}")
                print(f"{Fore.YELLOW}\tPlease ensure your Pipfile has a '[requires]' section with 'python_version'.{Fore.RESET}")
    except FileNotFoundError:
        print(f"{Fore.RED}\tError: Pipfile not found at {pipfile_path}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}\tError updating Pipfile {pipfile_path}: {e}{Fore.RESET}")


def rename_files(root: str, file_names: List[str], file_rules: Dict[str, str]) -> None:
    """
    Rename files according to specified rules.

    :param root: The root directory containing the files.
    :param file_names: List of filenames within the root directory.
    :param file_rules: Dictionary with old_name:new_name renaming pairs.
    """
    for file_name in file_names:
        for old_name, new_name in file_rules.items():
            if new_name is None: continue # Skip if new name is not provided
            file, ext = os.path.splitext(file_name)
            if old_name in file: # check if old_name substring is in the filename part
                repl_name = file_name.replace(old_name, new_name)
                old_path = os.path.join(root, file_name)
                new_path = os.path.join(root, repl_name)
                if os.path.exists(old_path) and old_path != new_path:
                    print(f"\t{Fore.BLUE}Rename file:{Fore.RESET} {old_path} to {new_path}")
                    os.rename(old_path, new_path)
                break # Move to the next file_name once a rule is applied

def rename_dirs(root: str, dirs: List[str], file_rules: Dict[str, str]) -> None:
    """
    Rename directories according to specified rules.

    :param root: The root directory containing the subdirectories.
    :param dirs: List of subdirectory names within the root directory.
    :param file_rules: Dictionary with old_name:new_name renaming pairs.
    """
    # Sort dirs by length descending to rename "foo-bar" before "foo" if "foo" is also a rule
    # This helps prevent partial renames that could break subsequent longer matches.
    # However, for simple exact matches as implemented, order might not be critical
    # unless a new_name itself could be an old_name in a subsequent rule for a different dir.
    # Current logic: only renames if dir_name == old_name.
    renamed_dirs_this_pass = set() # Keep track of what's been renamed to avoid multiple renames on same dir if new name matches another old rule
    for dir_name in list(dirs): # Iterate over a copy if modifying `dirs` list, though os.rename doesn't modify the list directly
        for old_name, new_name in file_rules.items():
            if new_name is None: continue
            if dir_name == old_name and old_name not in renamed_dirs_this_pass:
                old_path = os.path.join(root, old_name)
                new_path = os.path.join(root, new_name)
                if os.path.exists(old_path) and old_path != new_path:
                    print(f"{Fore.BLUE}\tRename directory:{Fore.RESET} {old_path} to {new_path}")
                    os.rename(old_path, new_path)
                    renamed_dirs_this_pass.add(new_name) # Add the new name as "processed" from perspective of old names
                    # Update the 'dirs' list in place if os.walk(topdown=False) re-reads it (it doesn't, it uses initial list)
                    # This is primarily to prevent trying to rename "old_name" again if it's gone.
                    # The main protection is `os.path.exists(old_path)`.
                break


def remove_files(root: str, file_names: List[str], file_patterns: List[str]) -> None:
    """
    Remove files that match given file_patterns within a specific root directory.
    """
    for filename in file_names:
        file_path = os.path.join(root, filename)
        if any(re.match(pattern, filename) for pattern in file_patterns):
            if os.path.exists(file_path): # Check existence before removal
                try:
                    print(f"{Fore.YELLOW}\tRemove file:{Fore.RESET} {filename}")
                    os.remove(file_path)
                    time.sleep(.1) # Brief pause, possibly for filesystem to catch up or visual effect
                except OSError as e:
                    print(f"{Fore.RED}\tError removing file {file_path}: {e}{Fore.RESET}")


def initalize(tgt_dir: str, new_pr_name: str, new_pg_name: str, new_alias: str, yes: bool = False, **kwargs) -> Tuple[str, str, str, str]:
    """
    Initialize and confirm user inputs for the project setup.
    """
    if tgt_dir is None:
        tgt_dir = input(f"{Fore.YELLOW}Enter target directory "
                        f"for your project (e.g., /path/to/parent_dir): {Fore.RESET}").strip()
    # If target directory ends with the new package name, assume user meant parent directory.
    # This logic might be too specific, consider if it's always desired.
    # if new_pg_name and tgt_dir.endswith(os.path.sep + new_pg_name):
    #     tgt_dir = os.path.dirname(tgt_dir)
    tgt_dir = os.path.expanduser(tgt_dir) # Expands ~ to user's home directory

    if new_pg_name is None:
        new_pg_name = input(f"{Fore.YELLOW}Enter new package name (e.g., mypackage): {Fore.RESET}").strip()
    
    if new_pr_name is None or new_pr_name == new_pg_name:
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
        if user_pr_name: # If user provided a new name
            new_pr_name = user_pr_name
        elif new_pr_name is None: # If it was None initially and user also skipped
            new_pr_name = new_pg_name # Default to package name if still None
            print(f"{Fore.CYAN}Project directory name will be '{new_pr_name}'.{Fore.RESET}")


    if new_alias is None:
        # Alias can be optional, if not provided, some replacement steps might skip it.
        # Or, default it to something, e.g., new_pg_name, or prompt.
        # For now, let it be None if not provided.
        print(f"{Fore.CYAN}No alias provided; alias-based replacements might be skipped.{Fore.RESET}")


    new_pr_dir_path = os.path.abspath(os.path.join(tgt_dir, new_pr_name))

    confirmation_message = (
        f"\n{Fore.CYAN}Project will be created with these names:{Fore.RESET}"
        f"\n  Project Directory: {Fore.YELLOW}{new_pr_dir_path}{Fore.RESET}"
        f"\n  Package Name:      {Fore.YELLOW}{new_pg_name}{Fore.RESET}"
        f"\n  Alias (if used):   {Fore.YELLOW}{new_alias or 'N/A'}{Fore.RESET}"
        f"\nContinue? [Y/n] (default is Y): "
    )
    
    if not yes: # If -y or similar flag was not passed to skip confirmation
        if input(confirmation_message).strip().lower() == "n":
            print(f"{Fore.RED}Operation canceled by user.{Fore.RESET}")
            sys.exit() # Use sys.exit for cleaner exit

    if 'protopy' in new_pr_dir_path and 'protopy' not in os.path.abspath(sts.project_dir): # Basic safety check
        # This check might need refinement. Avoid modifying the source 'protopy' if it's the template.
        # If 'new_pr_dir_path' IS the source protopy, something is wrong.
        print(f"{Fore.RED}Safety check: Target directory appears to be related to 'protopy' itself in an unexpected way.")
        print(f"Target: {new_pr_dir_path}{Fore.RESET}")
        print(f"To avoid accidental data loss, please choose a different target directory or project name.")
        sys.exit()
        
    return os.path.abspath(tgt_dir), new_pr_name, new_pg_name, new_alias


def copy_project(src_dir: str, tgt_dir: str, new_pr_name: str) -> None:
    """Copies the project using archive_main."""
    print(f"{Fore.CYAN}Copying project from '{src_dir}' to '{tgt_dir}' and renaming to '{new_pr_name}'...{Fore.RESET}")
    archive_main(**{
        'sources': [src_dir],
        'target': [tgt_dir],
        'rename': new_pr_name, # This renames the top-level copied folder to new_pr_name
        'comment': 'protopy initializer',
        'allYes': True, # Assuming non-interactive copy once confirmed
        'direct': 1,
        'verbose': 0 # Set to 1 or higher for more output from archive_main
    })
    print(f"{Fore.GREEN}Project copied successfully.{Fore.RESET}")

def copy_resources(tgt_dir: str, new_pr_name: str, pg_name:str='protopy') -> None:
    """
    from tgt_dir/new_pr_name/pg_name/resources copy arguments.py and settings.py 
    into to the new package directory tgt_dir/new_pr_name/pg_name.
    """
    pg_dir = os.path.join(tgt_dir, new_pr_name, pg_name)
    resources_dir = os.path.join(pg_dir, "resources")
    while not os.path.exists(resources_dir):
        print(f"{Fore.YELLOW}Resources directory {resources_dir} does not exist. Skipping resource copy.{Fore.RESET}")
        time.sleep(1) # Brief pause before copying resources, to allow any filesystem operations to settle
        continue
    print(f"Found:{Fore.YELLOW}{os.listdir(pg_dir)}{Fore.RESET}")

    # Copy arguments.py and settings.py from resources to the package directory
    for file_name in ["arguments.py", "settings.py", "Readme.md"]:
        src_file_path = os.path.join(resources_dir, file_name)
        if file_name == 'Readme.md':
            tgt_file_path = os.path.join(tgt_dir, new_pr_name, file_name)
        else:
            tgt_file_path = os.path.join(tgt_dir, new_pr_name, pg_name, file_name)

        if os.path.exists(src_file_path):
            shutil.copy2(src_file_path, tgt_file_path)
            print(f"{Fore.GREEN}Copied {file_name} to {tgt_file_path}{Fore.RESET}")
        else:
            print(f"{Fore.YELLOW}Resource file {src_file_path} does not exist. Skipping copy.{Fore.RESET}")
    # we can now remove the resources directory
    try:
        shutil.rmtree(resources_dir)
        print(f"{Fore.GREEN}Removed resources directory: {resources_dir}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}Error removing resources directory {resources_dir}: {e}{Fore.RESET}")
        # Optionally, handle specific exceptions like FileNotFoundError or PermissionError if needed


def replace_text_in_files(root: str, file_names: List[str], text_repls: Dict[str, str]) -> None:
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
                    if new_text is None: continue # Don't replace with None

                    # Direct, capitalized, and uppercase matches
                    new_contents = new_contents.replace(old_text, new_text)
                    if old_text.islower(): # Only do smart capitalization if old_text is all lower (common for identifiers)
                        new_contents = new_contents.replace(old_text.capitalize(), new_text.capitalize())
                    new_contents = new_contents.replace(old_text.upper(), new_text.upper())
                
                if new_contents != file_contents:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(new_contents)
                    print(f"{Fore.GREEN}\tUpdated text in:{Fore.RESET} {file_name}")
            except Exception as e: # Catch more general exceptions during file processing
                print(f"{Fore.RED}\tError processing file {file_path}: {e}{Fore.RESET}")

def remove_lines_in_files(root: str, file_names: List[str], *args, **kwargs) -> None:
    marker = '# clone_remove_line'
    for file_name in file_names:
        file_path = os.path.join(root, file_name)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                file_contents = file.read()
            if marker in file_contents:
                # If the file contains the specific line to remove, process it
                new_contents, removed_lines = [], []
                for line in file_contents.splitlines():
                    if marker in line: # Skip lines with this marker
                        removed_lines.append(line)
                    else:
                        new_contents.append(line)
                new_contents = '\n'.join(new_contents)
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_contents)
                print(  f"{Fore.GREEN}\tRemoved lines in:{Fore.RESET} {file_name}\n"
                        f"{removed_lines = }")

def setup_project(n_pr_dir: str, n_pg_name: str, *args, py_version: str = None, install: bool = False, **kwargs_setup) -> None:
    """Builds and optionally installs the new project."""
    setup_file = os.path.join(n_pr_dir, "setup.py")
    if not os.path.exists(setup_file):
        print(f"{Fore.YELLOW}No setup.py found in {n_pr_dir}. Skipping build and install steps.{Fore.RESET}")
        return

    setup_cfg_file = os.path.join(n_pr_dir, "setup.cfg")
    version = "0.1.0" # Default version if not found
    if os.path.exists(setup_cfg_file):
        try:
            with open(setup_cfg_file, "r") as f:
                text = f.read()
                version_match = re.search(r"version\s*=\s*(.*)", text)
                if version_match:
                    version = version_match.group(1).strip()
        except Exception as e:
            print(f"{Fore.YELLOW}Could not read version from setup.cfg: {e}. Using default '{version}'.{Fore.RESET}")

    print(f"{Fore.CYAN}\nBuilding project '{n_pg_name}' version '{version}'...{Fore.RESET}")
    # Using sys.executable to ensure using the python from the current environment
    setup_cmd = [sys.executable, "setup.py", "sdist", "bdist_wheel"] 
    print(f"{Fore.YELLOW}Now running:{Fore.RESET} {' '.join(setup_cmd)} in {n_pr_dir}")
    try:
        subprocess.check_call(setup_cmd, cwd=n_pr_dir) # Use check_call to raise error on failure
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Build failed: {e}{Fore.RESET}")
        return # Stop if build fails

    # List tar.gz (optional, for verification)
    dist_dir = os.path.join(n_pr_dir, "dist")
    tar_gz_pattern = os.path.join(dist_dir, f"{n_pg_name.replace('-', '_')}-{version}.tar.gz") # Handle hyphens vs underscores
    
    # Find the actual tar.gz file as names can vary slightly (e.g. underscore vs hyphen in package name)
    actual_tar_file = None
    if os.path.exists(dist_dir):
        for item in os.listdir(dist_dir):
            if item.endswith(".tar.gz") and n_pg_name in item.replace('-', '_') and version in item:
                actual_tar_file = os.path.join(dist_dir, item)
                break
    
    if actual_tar_file and os.path.exists(actual_tar_file):
        tar_list_cmd = ["tar", "--list", "-f", actual_tar_file]
        print(f"{Fore.YELLOW}\nContents of archive:{Fore.RESET} {' '.join(tar_list_cmd)}")
        try:
            subprocess.check_call(tar_list_cmd, cwd=n_pr_dir)
        except subprocess.CalledProcessError as e:
            print(f"{Fore.YELLOW}\tCould not list tar contents (tar command might not be available): {e}{Fore.RESET}")
        except FileNotFoundError:
            print(f"{Fore.YELLOW}\t'tar' command not found. Skipping listing archive contents.{Fore.RESET}")

    else:
        print(f"{Fore.YELLOW}\nCould not find .tar.gz archive matching pattern {tar_gz_pattern} to list contents.{Fore.RESET}")


    if not install:
        print(f"{Fore.GREEN}\nBuild complete. To install, re-run with the install flag or install manually.{Fore.RESET}")
        return

    print(f"{Fore.CYAN}\nInstalling project environment using pipenv...{Fore.RESET}")
    if py_version is None:
        print(f"{Fore.RED}Python version (-p) is required to set up the pipenv environment with --install.{Fore.RESET}")
        print(f"{Fore.YELLOW}Skipping pipenv install due to missing Python version.{Fore.RESET}")
        return

    pipenv_cmd = ["pipenv", "install", "--dev", "--python", py_version]
    print(f"{Fore.YELLOW}Now running:{Fore.RESET} {' '.join(pipenv_cmd)} in {n_pr_dir}")
    try:
        subprocess.check_call(pipenv_cmd, cwd=n_pr_dir)
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Pipenv install failed: {e}{Fore.RESET}")
        return
    except FileNotFoundError:
        print(f"{Fore.RED}'pipenv' command not found. Please ensure pipenv is installed and in your PATH.{Fore.RESET}")
        return

    # Test installation (basic import test or running actual tests)
    # For simplicity, this example doesn't run full unit tests here.
    # A simple import test could be: pipenv run python -c "import new_pg_name"
    print(f"{Fore.GREEN}\nDONE! Environment for '{n_pg_name}' should be set up.{Fore.RESET}")
    print(f"To activate, navigate to '{n_pr_dir}' and run 'pipenv shell'.")


def manage_replacements(old_params: Dict[str, str], new_params: Dict[str, str]) -> Dict[str, str]:
    """
    Create a dictionary for text replacements based on old and new project parameters.
    Relies on the order of values from .values() if used that way, or direct key mapping.
    This version assumes direct key mapping based on `project_params` structure.
    """
    text_repls = {}
    for key in old_params: # Iterate through keys of old_params ("pr_name", "pg_name", "alias")
        old_val = old_params.get(key)
        new_val = new_params.get(key) # new_params should also have "pr_name", "pg_name", "alias" as keys

        if old_val and new_val is not None: # Ensure both exist and new_val is not explicitly None
            text_repls[old_val] = new_val
            # Optional: Add capitalized and uppercase variants only if old_val is likely an identifier
            if old_val.islower() and old_val.isalpha(): # Simple check
                 text_repls[old_val.capitalize()] = new_val.capitalize()
                 text_repls[old_val.upper()] = new_val.upper()
            elif not old_val.islower() and not old_val.isupper(): # Mixed case or special chars
                 text_repls[old_val.upper()] = new_val.upper() # At least add uppercase
    return text_repls


def clone_and_install(*args, **kwargs_received): # Renamed kwargs for clarity
    """
    Main function to handle the renaming and removal of files and directories
    based on new project parameters.
    """
    # Extract parameters for initalize from kwargs_received
    # These keys should ideally match what the CLI argument parser produces (e.g. -pr -> 'new_pr_name' or 'pr')
    # Using .get(key) will default to None if key is missing; initalize handles None by prompting.
    p_tgt_dir = kwargs_received.get('tgt_dir')     # e.g., from CLI -t
    p_new_pr_name = kwargs_received.get('new_pr_name') # e.g., from CLI -pr
    p_new_pg_name = kwargs_received.get('new_pg_name') # e.g., from CLI -n
    p_new_alias = kwargs_received.get('new_alias')     # e.g., from CLI -a
    p_yes = kwargs_received.get('yes', False)          # e.g., from CLI -y

    tgt_dir, new_pr_name, new_pg_name, new_alias = initalize(
        p_tgt_dir, p_new_pr_name, p_new_pg_name, p_new_alias, yes=p_yes
    )
    new_project_path = os.path.join(tgt_dir, new_pr_name)
    print(f"\n{Fore.CYAN}Initialization complete. Project details:{Fore.RESET}")
    print(f"  Target Directory (parent): {tgt_dir}")
    print(f"  New Project Directory Name: {new_pr_name}")
    print(f"  New Package Name: {new_pg_name}")
    print(f"  New Alias: {new_alias or 'N/A'}")
    print(f"  Full Project Path: {new_project_path}")


    # Prepare parameters for renaming/replacement
    # old_params are from the template (global project_params)
    # new_params_for_replacement uses the same keys but with new values
    new_params_for_replacement = {
        "pr_name": new_pr_name,
        "pg_name": new_pg_name,
        "alias": new_alias,
        "port": str(kwargs_received.get('port')),
    }
    text_replacements = manage_replacements(project_params, new_params_for_replacement)
    
    # File/directory renaming rules primarily use direct old_name -> new_name mapping
    # for entities that match the template's names.
    file_renaming_rules = {}
    if project_params.get("pr_name") and new_pr_name:
        file_renaming_rules[project_params["pr_name"]] = new_pr_name
    if project_params.get("pg_name") and new_pg_name:
        file_renaming_rules[project_params["pg_name"]] = new_pg_name
    if project_params.get("alias") and new_alias:
        file_renaming_rules[project_params["alias"]] = new_alias

    copy_project(sts.project_dir, tgt_dir, new_pr_name)
    copy_resources(tgt_dir, new_pr_name)

    print(f"\n{Fore.BLUE}Starting restructuring in: {new_project_path}{Fore.RESET}")
    # Iterate topdown=True for dirs so parent is renamed before trying to walk its old name
    # However, os.walk(topdown=False) is often safer for modifications as you modify leaves first.
    # For renaming, if you rename a parent, the 'dirs' list for current 'root' might be outdated for subsequent iterations within os.walk.
    # A common pattern is to walk, collect changes, then apply. Or use topdown=False carefully.
    # Current rename_dirs/files operate on names *within* the current root, so topdown=False is fine.

    for root, dirs, files in os.walk(new_project_path, topdown=False):
        print(f"Processing directory: {root}")
        # Remove unwanted files first
        remove_files(root, files, path_patterns['file_patterns'])
        
        # Rename files, then directories (as file paths depend on directory names)
        # This order seems fine with topdown=False.
        rename_files(root, files, file_renaming_rules)
        rename_dirs(root, dirs, file_renaming_rules)

    # Second pass for text replacement after all renaming is done
    print(f"\n{Fore.BLUE}Replacing text content...{Fore.RESET}")
    for root, dirs, files in os.walk(new_project_path, topdown=True): # topdown=True for text replacement is fine
        replace_text_in_files(root, files, text_replacements)
        remove_lines_in_files(root, files)

    # Extract py_version and install for downstream functions from the original kwargs
    current_py_version = kwargs_received.get('py_version')
    current_install_flag = kwargs_received.get('install', False)

    pipfile_full_path = os.path.join(new_project_path, 'Pipfile')
    set_python_version_in_pipfile(
        pipfile_full_path,
        py_version=current_py_version
    )
    
    print(f"\n{Fore.CYAN}Debug Info:{Fore.RESET} Project Path='{new_project_path}', Package Name='{new_pg_name}'")
    # print(f"Args: {args}, Kwargs Received by clone_and_install: {kwargs_received}")
    
    setup_project(
        new_project_path,
        new_pg_name,
        *args, # Pass original args tuple if setup_project uses them
        py_version=current_py_version,
        install=current_install_flag
    )

def run_checks(*args, install: bool = False, py_version: str = None,
               port: str | int = None, **kwargs) -> None:
    """Checks python version format and required port."""
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

def main(*args, api:str=None, **kwargs) -> str:
    """
    Main entry point for the clone operation.
    Receives kwargs from the CLI parsing layer.
    """
    # This print helps to see what arguments this main function actually received.
    print(f"{Fore.MAGENTA}Initiating clone process with arguments: args={args}, kwargs={kwargs}{Fore.RESET}")

    # run_checks will use defaults if 'install' or 'py_version' are not in kwargs,
    # or use values from kwargs if provided.
    run_checks(*args, **kwargs)
    
    # clone_and_install will:
    # 1. Extract specific parameters for `initalize` from kwargs (e.g. 'tgt_dir', 'new_pr_name').
    #    If not found, `initalize` will prompt the user.
    # 2. Pass specific extracted parameters (e.g. 'py_version', 'install') to downstream functions.
    clone_and_install(*args, **kwargs)
    
    success_message = f"{Fore.GREEN}Cloning process completed successfully!{Fore.RESET}"
    print(f"\n{success_message}")
    return "Clone successful"


if __name__ == '__main__':
    # This is for direct execution testing of this script, e.g. python clone.py
    # In a real scenario, `main` would be called by your CLI framework (like proto.exe)
    print(f"{Fore.CYAN}Running clone.py directly for testing purposes.{Fore.RESET}")
    
    # Example test arguments (mimicking what the CLI parser might pass)
    test_kwargs = {
        'new_pr_name': 'myclonedproj',
        'new_pg_name': 'myclonedpackage',
        'new_alias': 'cloned',
        'tgt_dir': os.path.join(os.path.expanduser('~'), 'temp', 'clonetest'), # Create in user's temp
        'py_version': '3.11',
        'install': False, # Set to True to test installation
        'yes': True # Skip interactive prompts for testing
    }
    
    # Ensure target parent directory exists for testing
    os.makedirs(test_kwargs['tgt_dir'], exist_ok=True)
    
    # Mock sts.project_dir if not available or to control source for testing
    # Ensure sts.project_dir points to a valid template project structure.
    if not hasattr(sts, 'project_dir') or not os.path.isdir(sts.project_dir):
         print(f"{Fore.RED}sts.project_dir is not a valid directory. Mocking or aborting.{Fore.RESET}")
         # Create a dummy sts.project_dir for basic test run
         dummy_template_path = os.path.join(os.path.dirname(__file__), "dummy_protopy_template_for_clone_test")
         if not os.path.exists(dummy_template_path):
             os.makedirs(os.path.join(dummy_template_path, project_params["pg_name"]), exist_ok=True)
             with open(os.path.join(dummy_template_path, "Pipfile"), "w") as pf:
                 pf.write("[requires]\npython_version = \"3.9\"\n")
             with open(os.path.join(dummy_template_path, project_params["pg_name"], "__init__.py"), "w") as pfi:
                 pfi.write(f"# This is {project_params['pg_name']}\n")
             with open(os.path.join(dummy_template_path, "setup.py"), "w") as sf:
                 sf.write(f"from setuptools import setup\nsetup(name='{project_params['pg_name']}', version='0.1.0')\n")
             print(f"{Fore.YELLOW}Created a dummy template at: {dummy_template_path}{Fore.RESET}")
         sts.project_dir = dummy_template_path # Use dummy for test

    if not hasattr(sts, 'WHITE'): # Mock sts colors if settings isn't fully loaded
        class MockSts:
            def __init__(self):
                self.WHITE = self.RESET = self.YELLOW = self.RED = self.BLUE = self.GREEN = self.CYAN = self.MAGENTA = ""
        sts = MockSts()


    try:
        main(**test_kwargs)
    except SystemExit:
        print(f"{Fore.RED}Script exited early (e.g., due to user cancellation or error in checks).{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred during direct test run: {e}{Fore.RESET}")
        import traceback
        traceback.print_exc()