"""
script_path: src/protolib/test/core/gov/helpers/c15.py
paths: ["**/*.py"]
purpose: "Helper: c15 — deep-nesting via real indent column."
description: |-
  Tokenize-based check; ignores bracket-continuation lines (line_depth>0).
  Emits 'error' when the first non-skip token's column exceeds max_col,
  'warn' when it exceeds warn_col. Mutable state passed via dict so each
  helper function stays under c1 (≤7 lines).
update_rules: "Do not modify in clones. Thresholds arrive via **params from settings.yml."
"""
import io
import tokenize

_C15_SKIP = {tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT,
             tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL}


def run(*args, lines, warn_col, max_col, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    src = "\n".join(lines) + "\n"
    try: toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenizeError, IndentationError): return []
    return _walk(toks=toks, warn_col=warn_col, max_col=max_col)


def _walk(*args, toks, warn_col, max_col, **kwargs) -> list:
    """purpose: 'Iterate tokens with mutable state dict; collect indent records.'"""
    state = {"depth": 0, "line_depth": 0, "seen": set(), "out": []}
    for tok in toks:
        _step(tok=tok, state=state, warn_col=warn_col, max_col=max_col)
    return state["out"]


def _step(*args, tok, state, warn_col, max_col, **kwargs):
    """purpose: 'One token step — record line indent, then update bracket depth.'"""
    if tok.type in (tokenize.NEWLINE, tokenize.NL):
        state["line_depth"] = state["depth"]
        return
    if tok.type in _C15_SKIP: return
    _mark(tok=tok, state=state, warn_col=warn_col, max_col=max_col)
    _bracket(tok=tok, state=state)


def _mark(*args, tok, state, warn_col, max_col, **kwargs):
    """purpose: 'Emit warn/error for first token on a non-continuation line.'"""
    row, col = tok.start
    if row in state["seen"] or state["line_depth"] != 0: return
    state["seen"].add(row)
    if col > max_col: state["out"].append(_rec(row=row, col=col, level="error", thr=max_col))
    elif col > warn_col: state["out"].append(_rec(row=row, col=col, level="warn", thr=warn_col))


def _rec(*args, row, col, level, thr, **kwargs) -> dict:
    """purpose: 'Build one indent violation record.'"""
    return {"line": row, "scope": "module", "level": level,
            "technical_message": f"indent {col} spaces (>{thr})"}


def _bracket(*args, tok, state, **kwargs):
    """purpose: 'Track bracket nesting depth for line-continuation detection.'"""
    if tok.type != tokenize.OP: return
    if tok.string in "([{": state["depth"] += 1
    elif tok.string in ")]}": state["depth"] -= 1
