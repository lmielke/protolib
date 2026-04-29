"""
script_path: src/protolib/test/core/helpers/gov/c15.py
purpose: "[TO_DELETE] c15 — deep-nesting check. Flags real block indent depth beyond 4 levels."
description: "Skips bracket-continuation lines; errors at >5 levels (col >20)."
update_rules: "Do not modify in clones."
"""
import io, tokenize

_C15_SKIP = {tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT,
             tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL}


def _c15_deep_nesting(lines, rel, *args, **kwargs):
    """purpose: Flag real block-nesting depth — skip bracket-continuation lines."""
    warn, err = [], []
    try:
        toks = list(tokenize.generate_tokens(io.StringIO("".join(lines)).readline))
    except (tokenize.TokenizeError, IndentationError):
        return warn, err
    depth, line_depth, seen = 0, 0, set()
    for tok in toks:
        if tok.type in (tokenize.NEWLINE, tokenize.NL):
            line_depth = depth
            continue
        if tok.type in _C15_SKIP: continue
        row, col = tok.start
        if row not in seen and line_depth == 0:
            seen.add(row)
            if col > 20: err.append(f"line {row}: indent {col} spaces (>20, max 5 levels)")
            elif col > 16: warn.append(f"line {row}: indent {col} spaces (>4 levels)")
        if tok.type == tokenize.OP:
            if tok.string in "([{": depth += 1
            elif tok.string in ")]}": depth -= 1
    return warn, err
