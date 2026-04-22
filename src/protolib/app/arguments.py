"""
script_path: src/protolib/app/arguments.py
purpose: Parse protolib CLI arguments.
description: |-
  Call mk_args() to get a Namespace, then
  convert to dict via .__dict__. Avoid reusing existing arguments for
  unrelated purposes — add a new argument instead.
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
  - c41: "duplicate basename at app/arguments.py, core/arguments.py"
"""
import argparse, sys

_POSITIONAL = [
    {"name": "api", "metavar": "api", "help": "see protolib.apis"},
]

_OPTIONAL = [
    {"-pr": "--new_pr_name", "type": str,
     "help": "project name (top folder)"},
    {"-n": "--new_pg_name", "type": str,
     "help": "package name used inside project"},
    {"-a": "--new_alias", "type": str,
     "help": "package alias, if blank new_pg_name[:6] is used"},
    {"-t": "--tgt_dir", "type": str,
     "help": "target directory for clone"},
    {"-p": "--py_version", "type": str,
     "help": "python version for environment"},
    {"--port": None, "type": str,
     "help": "port for server.py (e.g. 9005)"},
    {"-m": "--model", "type": str,
     "help": "model name (default: gpt-3.5-turbo-0125)"},
    {"--install": None, "type": bool, "nargs": "?", "const": 1,
     "help": "run uv sync after clone"},
    {"-i": "--infos", "type": str, "nargs": "+",
     "help": "list of infos to retrieve (default: all)"},
    {"-d": "--detail", "type": int, "nargs": "?", "const": 1,
     "default": 0, "choices": range(0, 5),
     "help": "file system view verbosity (0-4)"},
    {"-v": "--verbose", "type": int, "nargs": "?", "const": 1,
     "default": 0, "help": "0:silent, 1:user, 2:debug"},
    {"--registry_url": None, "type": str,
     "help": "registry URL to register with"},
    {"--ttl": None, "type": int,
     "help": "heartbeat TTL in seconds (default: 30)"},
    {"--service_id": None, "type": str,
     "help": "service ID to discover (e.g. ollama, whisker)"},
    {"-y": "--yes", "type": bool, "nargs": "?", "const": 1,
     "help": "skip confirmation prompts during clone"},
]

def _add_positional(parser, *args, **kwargs):
    for spec in _POSITIONAL:
        parser.add_argument(spec["name"], metavar=spec.get("metavar"), help=spec.get("help"))

def _add_optional(parser, *args, **kwargs):
    for spec in _OPTIONAL:
        flags, kw = _parse_spec(spec, *args, **kwargs)
        parser.add_argument(*flags, **kw)

def _parse_spec(spec: dict, *args, **kwargs) -> tuple:
    flags = [k for k in spec if k.startswith("-")]
    long_val = spec.get(flags[0]) if len(flags) == 1 else None
    if long_val:
        flags.append(long_val)
    kw = {k: v for k, v in spec.items() if not k.startswith("-")}
    kw.setdefault("default", None)
    return flags, kw

def mk_args(*args, **kwargs):
    parser = argparse.ArgumentParser(description="run: python -m protolib info")
    _add_positional(parser, *args, **kwargs)
    _add_optional(parser, *args, **kwargs)
    return parser.parse_args()

def _extract_flag(action, *args, **kwargs) -> tuple:
    is_req = getattr(action, 'required', True) if not action.option_strings \
        else action.required
    return action.option_strings, action.dest, is_req

def _collect_action_flags(*args, action, flags: dict, **kwargs) -> None:
    opts, dest, is_req = _extract_flag(action, *args, **kwargs)
    for opt in opts:
        flags[opt] = is_req
    if not opts:
        flags[dest] = is_req

def get_required_flags(parser: argparse.ArgumentParser, *args, **kwargs) -> dict:
    flags = {}
    for action in parser._actions:
        if isinstance(action, argparse._StoreAction):
            _collect_action_flags(*args, action=action, flags=flags, **kwargs)
    return flags


if __name__ == "__main__":
    ns = mk_args()
    sys.stdout.write(get_required_flags(ns) + "\n")
