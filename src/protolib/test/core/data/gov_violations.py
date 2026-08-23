# Kitchen-sink governance fixture.
#
# Usage (manual):
#   1. cp src/protolib/test/core/data/gov_violations.py src/protolib/core/clone.py
#   2. cd ~/repos/protolib && uv run pytest src/protolib/test/core/test_governance.py -v
#   3. Confirm every cN + c_d* method emits >=1 warning or error
#   4. rm src/protolib/core/clone.py
#
# Coverage: c1..c36, c41, c_dfmt, c_dscope, c_dorph.
# Cannot fire from this single placement:
#   c18  — test_results.yaml is authoritative; unregistered modules are silently allowed
#          (would need an explicit {status: missing} entry for core/clone.py)
#   c40  — scope limited to helpers/; this file is in core/ after copy
#   c35 and c40 are mutually exclusive scopes and cannot co-fire.
"""
script_path: src/protolib/test/core/data/gov_violations.py
description: Fixture.
"""
# c26: relative import (auto-fix target)
from . import settings as _sts_rel
# c27: wildcard import
from os.path import *
# c32: stdlib logging import (forbidden outside helpers/printing)
import logging
# c10: flat import bypassing app/core/helpers/test layering
import protolib.nonexistent_subpkg as _flat
# c35: core module importing from app layer
from protolib.app import settings as _app_sts
import os, re

_LOG = logging.getLogger(__name__)

# c29: hardcoded absolute path
HARDCODED_PATH = "/home/lars/absolute/path"
# c11: line length > 95 characters (this line is deliberately longer than ninety-five characters yes)
OVERLONG_CONSTANT_NAME_TO_TRIGGER_C11 = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


# c13: module-level function before any class
# c5:  def without *args/**kwargs
def early_helper_before_class(value):
    real_line_1 = value
    real_line_2 = value + 1
    real_line_3 = value + 2
    return real_line_1 + real_line_2 + real_line_3


# c2:  one-line module-level def (candidate to inline)
def one_line_helper(*args, **kwargs): return 42


# c34: redefines strip_ansi_codes (canonical lives in helpers/printing.py)
def strip_ansi_codes(*args, s, **kwargs):
    return s


class FirstClass:
    """description: first class."""

    def kwargs_get_violation(self, *args, **kwargs):
        """description: c4 — direct kwargs access forbidden."""
        # c4: kwargs.get usage
        x = kwargs.get("x")
        return x

    def mutable_default_violation(self, *args, bucket=[], **kwargs):
        """description: c19 — mutable default arg list."""
        bucket.append(1)
        return bucket

    def long_method_violation(self, *args, **kwargs):
        """description: c1 — function body >10 code lines (error-level)."""
        a = 1
        b = 2
        c = 3
        d = 4
        e = 5
        f = 6
        g = 7
        h = 8
        i = 9
        j = 10
        k = 11
        return a + b + c + d + e + f + g + h + i + j + k

    def elif_chain_violation(self, *args, x, **kwargs):
        """description: c14 — more than 3 elif branches."""
        if x == 1:
            return 1
        elif x == 2:
            return 2
        elif x == 3:
            return 3
        elif x == 4:
            return 4
        elif x == 5:
            return 5
        return 0

    def deep_nesting_violation(self, *args, a, b, c, d, e, **kwargs):
        """description: c15 — indent beyond 4 levels (>16 spaces)."""
        if a:
            if b:
                if c:
                    if d:
                        if e:
                            return "very deep"
        return "shallow"

    def semicolon_violation(self, *args, **kwargs):
        """description: c6 — statements joined with ';'."""
        a = 1; b = 2
        return a + b

    def bare_except_violation(self, *args, **kwargs):
        """description: c28 — bare except."""
        try:
            return int("x")
        except:
            return 0

    def eval_violation(self, *args, **kwargs):
        """description: c7 — eval usage."""
        return eval("1 + 1")

    def local_import_violation(self, *args, **kwargs):
        """description: c25 — import inside a def body."""
        import sys
        return sys.path

    def pass_only_violation(self, *args, **kwargs):
        pass

    def raw_print_violation(self, *args, **kwargs):
        """description: c30 — raw print in non-exempt module."""
        print("raw print — should route through logprint")

    def inline_dict_violation(self, *args, **kwargs):
        """description: c36 — inline dict >8 entries inside a def."""
        big_map = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5,
                   "f": 6, "g": 7, "h": 8, "i": 9, "j": 10, "k": 11}
        return big_map

    def repeated_local_here_one(self, *args, **kwargs):
        """description: c21 — 'bucket_count' also in two peers."""
        bucket_count = 1
        return bucket_count

    def repeated_local_here_two(self, *args, **kwargs):
        """description: c21 — 'bucket_count' continues repeating."""
        bucket_count = 2
        return bucket_count

    def repeated_local_here_three(self, *args, **kwargs):
        """description: c21 — 'bucket_count' triggers repeated-locals warn."""
        bucket_count = 3
        return bucket_count


class SecondClass:
    """description: second class."""
    label = "second"


class ThirdClass:
    """
    description: third class.
    governance_exceptions:
      - c3: "module has 309 lines (>300)"
    """
    label = "third"


class FourthClass:
    """description: fourth class."""
    label = "fourth"


class FifthClass:
    """description: fifth class."""
    label = "fifth"


# c8: no __init__ anywhere in this file
# c12: brings total classes to 7 (>5)
class SixthClassNoInit:
    """description: c8 — no __init__ declared; c12 — 6th class in this module."""
    label = "sixth"


# c24: only 1 blank line before a top-level class (needs 2)

class SeventhClassTightSpacing:
    """description: c24 — only one blank line before this class (requires two)."""
    label = "seventh"


# c24: top-level def with 3 preceding blanks (needs 0 or 1)



def too_many_blanks_before(*args, **kwargs):
    """description: c24 — three preceding blanks (needs 0 or 1)."""
    return 1


def padding_one(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_two(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_three(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_four(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_five(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_six(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_seven(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_eight(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_nine(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_ten(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_eleven(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_twelve(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_thirteen(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


def padding_fourteen(*args, **kwargs):
    """description: padding to push total line count past 300 for c3."""
    value_one = 1
    value_two = 2
    return value_one + value_two


# c20: module has main() but no __name__ == "__main__" guard below

def main(*args, **kwargs):
    """description: entry point — deliberately missing __name__ guard below."""
    return 0
