"""
script_path: src/protolib/test/core/helpers/gov/c6.py
purpose: "[TO_DELETE] c6 — statement-on-semicolon check. Flags ';' that joins statements on one line."
description: "Joined statements hide control flow and disrupt per-line diffs; split them."
update_rules: "Do not modify in clones."
"""
import io, tokenize


def _c6_statement_semicolon(lines, rel, *args, **kwargs):
    """purpose: Tokenize and flag OP ';' tokens at statement boundaries."""
    warn, err = [], []
    try:
        toks = list(tokenize.generate_tokens(io.StringIO("".join(lines)).readline))
    except (tokenize.TokenizeError, IndentationError):
        return warn, err
    for tok in toks:
        if tok.type == tokenize.OP and tok.string == ';':
            warn.append(f"line {tok.start[0]}: statement-joined with ';' — split to new line")
    return warn, err
