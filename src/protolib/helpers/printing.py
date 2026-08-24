"""
script_path: src/protolib/helpers/printing.py
description: >-
  Provides ANSI-aware terminal utilities for colorized text, table rendering, and structured
  event logging. Applies regex-based colorization to tags, keywords, and markdown patterns
  within prompts. Routes warnings and errors to a file-backed logger while keeping informational
  messages console-only. Consumed by protolib modules that require formatted output or sound
  notifications.
tags:
- cli
- infra
- parsing
"""
import os, re, time, inspect, logging
from datetime import datetime as dt
from enum import Enum

from colorama import Fore, Back, Style
from tabulate import tabulate as tb
from textwrap import wrap as tw

import protolib.app.settings as sts

# ── platform guards ──────────────────────────────────────────
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False

# ── compiled patterns ────────────────────────────────────────
_ANSI_RE = re.compile(r'\x1b\[([0-9]+)(;[0-9]+)*m')

# ── logger setup ─────────────────────────────────────────────
event_logger = logging.getLogger("event_logger")
event_logger.setLevel(logging.INFO)
event_logger.propagate = False
if not event_logger.handlers:
    event_logger.addHandler(logging.NullHandler())


# ── Color enum & level mappings ──────────────────────────────
class Color(Enum):
    """description: 'ANSI foreground color tokens used by level and module color maps.'"""
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    GREEN = Fore.GREEN
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    RESET = Fore.RESET

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Calling signature.'"""
        return "Color(*args, **kwargs)"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Color name and ANSI value.'"""
        return f"Color({self.name}={self.value!r})"


LEVEL_COLORS = dict(
    error=Color.RED,
    warning=Color.YELLOW,
    info=Color.GREEN,
    debug=Color.RED,
    dev=Color.YELLOW,
)

MODULE_COLORS: dict[str, Color] = {}


# ── tag & keyword color maps for pretty_prompt ───────────────
_TAG_COLORS = {
    'deliverable': Back.MAGENTA,
    'rag_db_matches': Back.GREEN,
    'user_comment': Back.YELLOW,
    'previous_responses': Back.CYAN,
    'sample': Back.CYAN,
    'io_template': Back.CYAN,
    'INST': Back.CYAN,
    'poluted_text': Back.CYAN,
}

_DIM_KEYWORDS = ('__SAMPLE', '__RESPONSE SAMPLE', '__TEXT SAMPLE')

_MD_PATTERNS = [
    (r'^# ([A-Z1-9].+)$', f"{Back.BLUE}# \\1{Style.RESET_ALL}", re.MULTILINE),
    (r'^## (.+)$', f"{Fore.BLUE}## \\1{Fore.RESET}", re.MULTILINE),
    (r'^.?```(\w+)?$', f"{Fore.MAGENTA}``` \\1{Fore.RESET}", re.MULTILINE),
    (r'(.*)(https?://[^\s\'_\"]+)(.*)', f"\\1{Fore.MAGENTA}\\2{Fore.RESET}\\3", 0),
]

# ── threshold table for normalize_max_chars ──────────────────
_MAX_CHARS_THRESHOLDS = [(50, 5), (128, 4), (300, 3), (1200, 2)]

# ── sound dispatch for play_sound ────────────────────────────
_SOUND_MAP = {
    "PROMPT":    [(600, 150), (1000, 150)],
    "PROMPT0":   [(600, 150)],
    "PROMPT1":   [(1000, 150)],
    "PROMPT2":   [(1300, 150)],
    "RESPONSE":  [(1000, 150), (800, 150), (600, 150)],
    "RESPONSE0": [(1000, 100)],
    "RESPONSE1": [(1200, 100)],
    "RESPONSE2": [(1600, 100)],
    "HAPPY":     [(1400, 100), (1600, 100), (2000, 100)],
    "ERROR":     [(200, 150), (100, 550)],
}


# ── internal helpers ─────────────────────────────────────────

def _colorize_tags(text: str, *args, **kwargs) -> str:
    """description: 'Apply background color to recognized XML-style tag names in text.'"""
    for name, color in _TAG_COLORS.items():
        text = text.replace(f'{name}>', f"{color}{name}{Style.RESET_ALL}>")
    return text

def _colorize_keywords(text: str, *args, **kwargs) -> str:
    """description: 'Dim and whiten sample/response keywords; highlight Strategy Prompt.'"""
    for kw in _DIM_KEYWORDS:
        styled = f"__{Style.DIM}{Fore.WHITE}{kw[2:]}{Style.RESET_ALL}{Style.RESET_ALL}"
        text = text.replace(kw, styled)
    replacement = f"{Fore.YELLOW}Strategy Prompt{Style.RESET_ALL}"
    text = text.replace('Strategy Prompt', replacement)
    return text

def _colorize_markdown(text: str, *args, **kwargs) -> str:
    """description: 'Apply ANSI color to markdown headings, code fences, and URLs.'"""
    for pattern, replacement, flags in _MD_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=flags)
    return text

def _format_value(value, *args, **kwargs) -> str:
    """description: 'Wrap str/dict/list values for display; convert others via str().'"""
    if isinstance(value, str): return wrap_text(value, *args, **kwargs)
    if isinstance(value, dict):
        joined = '\n'.join(f"{Fore.CYAN}{k}{Fore.RESET}: {str(v)}" for k, v in value.items())
        return wrap_text(joined, *args, **kwargs)
    if isinstance(value, list): return wrap_text('\n'.join([str(v) for v in value]), *args, **kwargs)
    return str(value)

def _print_unrolled_prompts(k, vs, *args, **kwargs):
    """description: 'Print prompt list key with count then each truncated prompt.'"""
    print(f"\t{k = }: {len(vs)}")
    for i, prompt in enumerate(vs):
        start = '\n' if i != 0 else ''
        prompt = '\n\t\t'.join(prompt[:200].split('\n'))
        print(f"{start}\t\t{Fore.MAGENTA}{i}{Fore.RESET}: {prompt[:150]}")

def _print_df_line(line, *args, i: int, total: int, color=Fore.MAGENTA, sum_color=None, **kwargs):
    """description: 'Print one dataframe row; colorize header and optional summary row.'"""
    if i <= 1:
        print(f"{color}{line}{Fore.RESET}")
    elif sum_color and i == total - 1:
        sep = f"{sum_color}{'_ ' * (len(line) // 2)}{Style.RESET_ALL}"
        print(f"{sep}\n{line}")
    else:
        print(line)

def _caller_info(*args, **kwargs) -> tuple[str, str, str]:
    """description: 'Return (module, class, function) names two frames up the call stack.'"""
    f = inspect.currentframe().f_back.f_back
    cls = f.f_locals.get("self")
    mod = f.f_globals.get("__name__", "")
    return mod, (cls.__class__.__name__ if cls else ""), f.f_code.co_name

def _ready_logger(*args, p: str | None, **kwargs) -> None:
    """
    description: Attach file handler only once error.log is ready.
    """
    if not (isinstance(p, str) and p.endswith("error.log")): return
    if any(not isinstance(h, logging.NullHandler) for h in event_logger.handlers): return
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    h = logging.FileHandler(p, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    event_logger.addHandler(h)

def _log_style(level: str, *args, mod: str = "", **kwargs):
    """description: 'Resolve ANSI style and Color for a log level or module name.'"""
    style = (Style.BRIGHT if level in ("debug", "dev")
             else Style.NORMAL if level else Style.DIM)
    color = LEVEL_COLORS.get(level, MODULE_COLORS.get(mod, LEVEL_COLORS["info"]))
    return style, color

def _log_emit(msg, *args, level: str, origin: str, console_log: bool = True, **kwargs):
    """description: 'Route warning/error to file logger and print to console if enabled.'"""
    style, color = _log_style(level, *args, **kwargs)
    if level in ("warning", "error"):
        log_fn = getattr(event_logger, level, event_logger.warning)
        log_fn(f"{origin}:\n{msg}\n")
    if console_log:
        print(f"\n{color.value}{style}{origin}:\n{Fore.RESET}{msg}{Style.RESET_ALL}\n")
    return msg


# ── public API ───────────────────────────────────────────────

def normalize_max_chars(max_chars: int, text, *args, **kwargs):
    """
    description: Re-compute max_chars to produce a minimum of ~3 wrapped lines.
    """
    for bound, divisor in _MAX_CHARS_THRESHOLDS:
        if len(text) <= bound:
            return max_chars // divisor
    return int(max_chars * 2)

def wrap_text(text: str, *args, max_chars: int = sts.table_max_chars, **kwargs):
    """description: 'Wrap text to max_chars width, normalizing threshold first.'"""
    max_chars = normalize_max_chars(max_chars, text, *args, **kwargs)
    if not isinstance(text, str) or len(text) <= max_chars: return text
    wrapped = ['\n'.join(tw(l, max_chars)) if len(l) > max_chars else l
               for l in text.split('\n')]
    return '\n'.join(wrapped).strip()

def wrap_table(d: dict, *args, **kwargs):
    """description: 'Return copy of dict with all values wrapped to display width.'"""
    tbl_dict = dict(**d)
    for kk, vs in d.items(): tbl_dict[kk] = _wrap_value(vs, *args, **kwargs)
    return tbl_dict

def _wrap_value(vs, *args, **kwargs):
    """description: 'Wrap a single str/dict/list value; pass non-text types through.'"""
    if isinstance(vs, str): return wrap_text(vs, *args, **kwargs)
    if isinstance(vs, dict):
        joined = '\n'.join(f"{Fore.CYAN}{k}{Fore.RESET}: {str(v)}" for k, v in vs.items())
        return wrap_text(joined, *args, **kwargs)
    if isinstance(vs, list): return wrap_text('\n'.join(str(v) for v in vs), *args, **kwargs)
    return vs

def strip_ansi_codes(text: str, *args, **kwargs) -> str:
    r"""
    description: Strip ANSI escape sequences, carriage returns, and unescape \n.
    """
    cleaned = _ANSI_RE.sub('', text)
    return cleaned.replace('\r', '').replace('\\n', '\n')

def clean_pipe_text(text: str, *args, **kwargs) -> str:
    r"""
    description: Keep Unicode intact; unescape \n/\t; strip ANSI; fix cp1252-mojibake.
    """
    t = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', text)
    for a, b in [('\\r\\n', '\r\n'), ('\\n', '\n'), ('\\r', '\r'), ('\\t', '\t')]:
        t = t.replace(a, b)
    if 'â' in t:
        try: t = t.encode('latin-1').decode('utf-8')
        except Exception: pass
    return t

def pretty_prompt(prompt: str, *args, verbose: int = 0, **kwargs) -> str:
    """description: 'Strip ANSI/pipe artifacts then apply tag, keyword, and markdown colors.'"""
    prompt = re.sub(r'<user_comment>\s*</user_comment>', '', prompt, flags=re.MULTILINE)
    p = clean_pipe_text(strip_ansi_codes(prompt, *args, **kwargs), *args, **kwargs)
    p = _colorize_markdown(
        _colorize_keywords(_colorize_tags(p, *args, **kwargs), *args, **kwargs), *args, **kwargs)
    if verbose >= 1: print(f"{p.strip()}")
    return p

def pretty_dict(name: str, d: dict, *args, color=Fore.CYAN, **kwargs):
    """description: 'Print dict key-value pairs with colored header and key names.'"""
    print(f"\n{color}{name} {Fore.RESET}\n{'*' * len(name)}")
    for k, v in d.items():
        print(f"{color}{k}: {Fore.RESET}{v}")

def dict_to_table(name: str, d: dict, *args, **kwargs):
    """description: 'Render dict as a two-column tabulate table with colored underline.'"""
    tbl_dict = wrap_table(d, *args, **kwargs)
    colored_table_underline(
        tb(tbl_dict.items(), headers=[f'name: {name}', 'value'], tablefmt='simple'),
        *args, **kwargs)

def records_to_table(records: list, *args, **kwargs):
    """description: 'Render list of dicts as a tabulate table with colored underline.'"""
    wrapped = [wrap_table(r, *args, **kwargs) for r in records]
    headers = records[0].keys()
    table = [r.values() for r in wrapped]
    colored_table_underline(tb(table, headers=headers), *args, **kwargs)

def colored_table_underline(tbl, *args, up_to: int = 0, color=Fore.CYAN, **kwargs):
    """description: 'Print table with header rows colored up to up_to index.'"""
    print('\n')
    for i, line in enumerate(tbl.split('\n')):
        if i <= up_to:
            print(f"{color}{line}{Fore.RESET}")
        else:
            print(line)

def dict_to_table_v(d: dict, *args, **kwargs):
    """
    description: Prints dict with keys as column headers and values as rows.
    """
    row = [_format_value(v, *args, **kwargs) for v in d.values()]
    colored_table_underline(
        tb([row], headers=list(d.keys()), tablefmt='simple'), *args, **kwargs)

def unroll_print_dict(d: dict, unroll_key: str = 'prompts', *args, **kwargs):
    """description: 'Print dict entries; expand unroll_key as indexed prompt list.'"""
    for k, vs in d.items():
        if k == 'service_endpoint':
            print(f"\t{k = }: {Fore.MAGENTA}{vs}{Fore.RESET}")
        elif k == unroll_key:
            _print_unrolled_prompts(k, vs, *args, **kwargs)
        else:
            print(f"\t{k = }: {vs}")

def pretty_print_df(df, *args, **kwargs):
    """
    description: Takes a dataframe and prints it in a colored pretty format.
    """
    lines = tb(df, headers='keys', tablefmt='simple').split('\n')
    for i, line in enumerate(lines):
        _print_df_line(line, *args, i=i, total=len(lines), **kwargs)

def play_sound(status: str, *args, **kwargs):
    """
    description: Plays a short acoustic signal based on the given status.
    """
    if not SOUND_AVAILABLE:
        return
    for freq, dur in _SOUND_MAP.get(status, []):
        winsound.Beep(freq, dur)
    if status == "HAPPY":
        time.sleep(.1)

def logprint(msg: str, *args, level: str = None, **kwargs) -> str:
    """
    description: INFO/DEBUG remain console-only.
    """
    assert getattr(sts, "error_path", None), "sts.error_path not set"
    _ready_logger(*args, p=sts.error_path, **kwargs)
    p_level = (level or "").lower()
    mod, cls, func = _caller_info(*args, **kwargs)
    mod = mod.split(".")[-1]
    origin = f"{mod}.{cls + '.' if cls else ''}{func} {p_level.upper()}"
    return _log_emit(
        msg, *args, level=p_level or "info", origin=origin, mod=mod, **kwargs)
