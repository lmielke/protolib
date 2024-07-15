# collections.py
import json, os, re, shutil, subprocess, sys, textwrap, time, yaml
from contextlib import contextmanager
from pathlib import Path
from tabulate import tabulate as tb
from datetime import datetime as dt


import protopy.settings as sts

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


def _handle_integer_keys(self, intDict) -> dict:
    """
    helper function for api calls
    api endpoint calls are called by providing the relevant api api index
    as an integer. During serialization its converted to string and therefore
    has to be reconverted to int here
    """
    intDict = {int(k) if str(k).isnumeric() else k: vs for k, vs in intDict.items()}
    return intDict


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


def get_sec_entry(d, matcher, ret="key", current_key=None) -> str:
    if isinstance(d, dict):
        for key, value in d.items():
            if key == matcher:
                return current_key if ret == "key" else d[key]
            elif isinstance(value, dict):
                result = get_sec_entry(value, matcher, ret, current_key=key)
                if result is not None:
                    return result
    return None


def load_yml(testFilePath, *args, **kwargs):
    with open(testFilePath, "r") as f:
        return yaml.safe_load(f)


def load_str(testFilePath, *args, **kwargs):
    with open(testFilePath, "r") as f:
        return f.read()


def group_text(text, charLen, *args, **kwargs):
    # performs a conditional group by charLen depending on type(text, list)
    if not text:
        return "None"
    elif type(text) is str:
        texts = handle_existing_linebreaks(text, *args, **kwargs)
        texts = [textwrap.wrap(t, width=charLen) for t in texts]
        texts = ['\n'.join(t) for t in texts]
        # this removes empty lines from file hierarchy display
        # texts = [t for t in texts 
        #             if (not re.match(sts.hierarchy_empties, t) or not t.endswith('|'))]
        text = '\n'.join(texts)
    return text
        

def handle_existing_linebreaks(text, *args, **kwargs):
    # NOTE: "psql" tables will correctly split, so they are reconstructed as original
    texts = re.split(sts.split_flags, text)
    texts = [t.strip() for t in texts if t]
    texts = [t.replace('  ', ' ') if not t.startswith('|') else t for t in texts if t]
    for i, t in enumerate(texts):
        # print(f"\t{i}: {t = }")
        if t == '.':
            texts[i-1] = texts[i-1].strip() + '.'
            texts[i] = ''
        elif re.search(r'^-|^\d\.', t):
            try:
                texts[i+1] = f'\n{t} ' + texts[i+1]
                texts[i] = ''
            except IndexError:
                pass
    texts = [t.strip().replace('\n', ' ') for t in texts if t]
    texts = [re.sub(r'(\w)(\s{2,})(\w)', r'\1 \3', t) for t in texts]
    texts = [re.sub(r'([.])(\s{2,})(\w)', r'\1 \3', t) for t in texts]
    return texts

def restore_existing_linebreaks(text, *args, **kwargs) -> str:
    """
    Adds a line break before numbered list items, preserving existing line breaks.

    Args:
        text (str): The text where line breaks and numbered lists will be adjusted.

    Returns:
        str: The text with the modified line breaks.
    """
    # print(re.findall(r'<lb>\s*(\d+\.\s)', text))
    text = re.sub(r'(<lb>\s*)(\d+\.\s)', r'\n\2', text)
    text = re.sub(r'(<lb>\s*)(-\s*)', r'\n\2', text)
    text = re.sub(r'(<lb>\s*)(<code_block_\d+>\s*)(<lb>\s*)', r'\n\2\n', text)
    text = re.sub(r'\n(\n\d+\.\s|\n-\s|\n<code_block_\d+\s)', r'\1', text)
    text = re.sub(r'\n<lb>\s*', r'\n', text)
    text = re.sub(r'\s*<lb>\s*', r' ', text)
    return text

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

def custom_ignore(ignored):
    """
    Custom ignore function for shutil.copytree.

    Args:
        ignored (set): Set of directory paths to ignore.

    Returns:
        callable: A function that shutil.copytree can use to determine what to ignore.
    """
    def _ignore_func(dir, cs):
        return set(c for c in cs if os.path.join(dir, c) in ignored)
    return _ignore_func


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

def ppm(msg, *args, **kwargs):
    """
    Pretty print messages
    """
    # contents a printed without headers and table borders
    tbl_params = {'tablefmt': 'plain', 'headers': ''}
    msg["content"] = pretty_print_messages([msg["content"]], *args, **tbl_params, **kwargs)
    return pretty_print_messages([msg], *args, **kwargs)

def pretty_print_messages(messages, *args, verbose:int=0, clear=True, save=True, **kwargs):
    """
    Takes self.messages and prints them as a tabulate table with two columns 
    (role, content)
    """
    tbl = to_tbl(messages, *args, verbose=verbose, **kwargs)
    # use subprocess to clear the terminal
    if clear: subprocess.run(["cmd.exe", "/c", "cls"])
    # print(printable)
    if save: save_table(tbl, *args, **kwargs)
    return tbl

def to_tbl(data, *args, headers=['EXPERT', 'MESSAGE'], tablefmt='simple', **kwargs):
    tbl = to_list(data, *args, **kwargs)
    return tb(tbl, headers=headers, tablefmt=tablefmt)

def to_list(data, *args, **kwargs):
    tbl = []
    for m in data:
        tbl.append(prep_line(m, *args, **kwargs))
    return tbl

def prep_line(m, *args, **kwargs):
    name, content = m.get('name'), m.get('content', m.get('text'))
    role, watermark, mId = m.get('role'), m.get('watermark'), m.get('mId')
    return (f"{mId} {color_expert(name, role, watermark)}", content)

def color_expert(name, role, watermark, *args, **kwargs):
    try:
        color = sts.experts.get(name.lower(), {}).color_code
    except AttributeError:
        color = sts.RED
    name = f"{watermark if watermark else ''} {color}{name}:{sts.ST_RESET}".strip()
    return name

def colorize_code_blocks(code_blocks:dict, *args, fm:str='pretty', **kwargs):
    # colorize code blocks
    colorized = {}
    for name, (language, block) in code_blocks.items():
        if fm in ['pretty', 'colored']:
            preped = [f"{sts.code_color}{b}{sts.ST_RESET}" for b in block.split('\n') if b]
        else:
            preped = [f"{b}" for b in block.split('\n') if b]
        block = '\n'.join(preped)
        # block = '\t' + block.replace('\n', '\t\t')
        language = f"{sts.language_color}{language}{sts.ST_RESET}"
        colorized[name] = '´´´' + language + '\n\n' + block + '\n\n´´´'
    return colorized

def _decolorize(line, *args, **kwargs):
    line = line.replace(sts.YELLOW, "").replace(sts.BLUE, "").replace(sts.GREEN, "")
    line = line.replace(sts.RED, "").replace(sts.CYAN, "").replace(sts.WHITE, "")
    line = line.replace(sts.DIM, "").replace(sts.RESET, "").replace(sts.ST_RESET, "")
    return line

def save_table(tbl, *args, **kwargs):
    table_path = os.path.join(sts.chat_logs_dir, f"{sts.session_time_stamp}_chat.log")
    tbl = '\n'.join([_decolorize(l) for l in tbl.split('\n')])
    with open(table_path, 'w', encoding='utf-8') as f:
        f.write(tbl)


def hide_tags(text, *args, verbose:int=0, **kwargs):
    """
    Takes a string and removes all tag enclosed contents from the string

    Args:
        text (str): The text to remove tags from.
        tags (list, optional): The tags to remove. Defaults to None.
            Options:
                ['pg_info', ]: removes everything between <pg_info> and </pg_info>
    """
    for start, end in sts.tags.values():
        # the replacement term depends on verbosity. If verbose, add a newline
        # otherwise remove the tag completely.
        if verbose == 0:
            start, replacement = r"\s*" + start, r''
        elif verbose <= 1:
            replacement = f"{sts.CYAN}{start}...{end}{sts.ST_RESET}"
        else:
            replacement = f'\n{sts.CYAN}\\1{sts.ST_RESET}\n'
        # replacement = r'' if verbose < 1 else f"{start}...{end}" if verbose < 2 else r'\n\1\n'
        # flags must be set to re.DOTALL to match newline characters and multiline strings
        text = re.sub(fr'({start}.*?{end})', replacement, text, flags=re.DOTALL)
    return '\n' + text

def prettyfy_instructions(instructs, tag:str='instructs', *args, verbose:int=1, **kwargs):
    # instructions are cyan
    if verbose >= 2:
        prettyfied = group_text(instructs, sts.table_width).replace('\n', '\n\t')
    elif verbose >= 1:
        prettyfied = group_text(instructs, sts.table_width).replace('\n', '\n\t')[:sts.table_width*3]
        prettyfied += f"\n\t...[hidden {len(instructs) - sts.table_width*3} characters], verbose={verbose}"
    else:
        return ''
    return add_tags('\t' + prettyfied, tag)

def add_tags(content, tag, *args, **kwargs):
    """
    Adds tags to the message content.
    """
    if not tag:
        return content
    start, end, color = sts.tags.get( tag, ('', '', '') )
    return f"{start}\n{content}\n{end}"

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

def check_range_exists(text:str, in_range:tuple[int, int]):
    """
    Checks if a line exists in a text string.

    Args:
        text (str): The text to check.
        in_range (tuple[int, int]): The line numbers to check.

    Returns:
        bool: True if the line exists, False otherwise.
    """
    lines = text.split('\n')
    return all(0 <= line < len(lines) for line in in_range)