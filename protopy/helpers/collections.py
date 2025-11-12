# collections.py
import json, os, pyttsx3, re, shutil, subprocess, sys, textwrap, time, yaml
from contextlib import contextmanager
from pathlib import Path
from tabulate import tabulate as tb
from datetime import datetime as dt

import protopy.settings as sts

def _speak_message(message: str, *args, **kwargs):
    """Uses pyttsx3 to speak a given message."""
    try:
        engine = pyttsx3.init()
        engine.say(message)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"Text-to-speech failed: {e}")

def unalias_path(work_path: str) -> str:
    """
    repplaces path aliasse such as . ~ with path text
    """
    if not any([e in work_path for e in [".", "~", "%"]]):
        return work_path
    work_path = work_path.replace(r"%USERPROFILE%", "~")
    work_path = work_path.replace("~", os.path.expanduser("~"))
    if work_path.startswith(".."):
        work_path = os.path.join(os.path.dirname(os.getcwd()), work_path[3:])
    elif work_path.startswith("."):
        work_path = os.path.join(os.getcwd(), work_path[2:])
    work_path = os.path.normpath(os.path.abspath(work_path))
    return work_path

def prep_path(work_path: str, file_prefix=None) -> str:
    work_path = unalias_path(work_path)
    if os.path.exists(work_path):
        return work_path
    # check for extensions
    extensions = ["", sts.eext, sts.fext]
    name, extension = os.path.splitext(os.path.basename(work_path))
    for ext in extensions:
        work_path = unalias_path(f"{name}{ext}")
        if os.path.isfile(work_path):
            return work_path
    return f"{name}{extension}"

def find_dict_entry(d: dict, matcher: str) -> dict | None:
    for k, v in d.items():
        if k == matcher:
            return {k: v}
        if isinstance(v, dict):
            r = find_dict_entry(v, matcher)
            if r:
                return r
    return None

def group_text(text, charLen, *args, **kwargs):
    # performs a conditional group by charLen depending on type(text, list)
    if not text:
        return "None"
    elif type(text) is str:
        text = handle_existing_linebreaks(text, *args, **kwargs)
        # print(f"0: {text = }")
        text = '\n'.join(textwrap.wrap(text, width=charLen))
        # print(f"1: {text = }")
        text = restore_existing_linebreaks(text, *args, **kwargs)
        # print(f"2: {text = }")
        # text = text.replace(' <lb> ', '\n').replace('<lb>', '\n')
        # text = text.replace('<tab>', '\t')
    elif type(text) is list:
        text = "\n".join(textwrap.wrap("\n".join([t for t in text]), width=charLen))
    else:
        print(type(text), text)
    return '\n' + text

def collect_ignored_dirs(source, ignore_dirs, *args, **kwargs):
    """
    Uses os.walk and regular expressions to collect directories to be ignored.

    Args:
        source (str): The root directory to start searching from.
        ignore_dirs (list of str): Regular expressions for directory paths to ignore.

    Returns:
        set: A set of directories to be ignored.
    """
    ignored = set()
    regexs = [re.compile(d) for d in ignore_dirs]

    for root, dirs, _ in os.walk(source, topdown=True):
        for dir in dirs:
            dir_path = os.path.join(root, dir).replace(os.sep, '/')
            if any(regex.search(dir_path) for regex in regexs):
                ignored.add(os.path.normpath(dir_path))
    return ignored

@contextmanager
def temp_chdir(target_dir: str) -> None:
    """
    Context manager for temporarily changing the current working directory.

    Parameters:
    target_dir (str): The target directory to change to.

    Yields:
    None
    """
    original_dir = os.getcwd()
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(original_dir)

def strip_ansi_codes(text: str) -> str:
    """
    Strip ANSI escape sequences from a text string.
    Args:
        text (str): Text containing ANSI escape codes.
    Returns:
        str: Text with ANSI codes removed.
    """
    ansi_escape = re.compile(r'\x1b\[([0-9]+)(;[0-9]+)*m')
    return ansi_escape.sub('', text)

def _find_file_path(raw_path=None, *args, project_dir=None, max_depth=5, verbose:int=0, **kwargs):
    if not raw_path:
        return None
    pr_dir = project_dir or sts.project_dir
    root_depth = pr_dir.count(os.sep)
    file_name = os.path.basename(raw_path)
    def ignored(d):
        d = d.strip()
        return any(d == i or d.endswith(i.strip('*')) for i in sts.ignore_dirs)
    for root, dirs, files in os.walk(pr_dir, topdown=True):
        if ignored(os.path.basename(root)):
            dirs.clear()
            continue
        if root.count(os.sep) - root_depth >= max_depth:
            dirs.clear()
            continue
        if file_name in files:
            if verbose:
                print(f"\ncontracts._find_file_path: Found {file_name = } at {root = }")
            return os.path.join(root, file_name)
        dirs[:] = [d for d in dirs if not ignored(d)]
    return None
