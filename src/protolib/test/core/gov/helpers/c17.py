"""
script_path: src/protolib/test/core/gov/helpers/c17.py
paths: ["**/*.py"]
purpose: "Helper: c17 — module docstring description must meet minimum length."
description: |-
  Reads the module docstring; strips the script_path: line; counts words
  and sentence terminators in the remainder. Emits 'warn' when both
  thresholds fail (passes if EITHER min_words OR min_sentences is met).
  Docstring presence and front-matter shape are c90_1's job — c17 is
  description-length only.
update_rules: "Do not modify in clones. Thresholds arrive via **params from settings.yml."
"""
import ast
import re


def run(*args, tree, min_words, min_sentences, **kwargs) -> list[dict]:
    """purpose: 'Return list of violation records — empty list ⇒ clean.'"""
    ds = ast.get_docstring(tree)
    if not ds: return []
    if _is_long_enough(ds=ds, min_words=min_words, min_sentences=min_sentences): return []
    msg = f"module docstring too short (≥{min_words} words or ≥{min_sentences} sentences)"
    return [{"line": 1, "scope": "module", "level": "warn", "technical_message": msg}]


def _is_long_enough(*args, ds, min_words, min_sentences, **kwargs) -> bool:
    """purpose: 'Description meets word-count OR sentence-count threshold.'"""
    desc = re.sub(r'script_path:\s*\S+\n?', '', ds).strip()
    words = len(desc.split())
    sentences = sum(1 for c in desc if c in ".!?")
    return words >= min_words or sentences >= min_sentences
