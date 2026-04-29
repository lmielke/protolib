"""
script_path: src/protolib/test/core/gov/helpers/c6.py
paths: ["**/*.py"]
purpose: "Helper: c6 — `;` joining statements on one line is forbidden."
description: |-
  Tokenize-based; OP ';' tokens emitted by the tokenizer are statement
  separators on a single physical line. Each one produces a 'warn'.
  Tokenize errors fail loud (silent return preserves legacy behavior).
update_rules: "Do not modify in clones. No thresholds."
"""
import io
import tokenize


def run(*args, lines, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    src = "\n".join(lines) + "\n"
    try: toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenizeError, IndentationError): return []
    return [_rec(line=t.start[0]) for t in toks
            if t.type == tokenize.OP and t.string == ';']


def _rec(*args, line, **kwargs) -> dict:
    """purpose: 'Build one warn record for a `;`-joined line.'"""
    return {"level": "warn", "line": line, "scope": "def",
            "technical_message": "statement-joined with ';' — split to new line"}
