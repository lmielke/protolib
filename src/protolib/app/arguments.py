"""
script_path: src/protolib/app/arguments.py
description: >-
  Defines the protolib CLI argument schema and parsing logic using argparse. Exposes mk_args()
  to return a Namespace object that callers convert to a dictionary. Maintains a strict separation
  between positional and optional flags, including project setup, server configuration, and
  service discovery parameters.
tags:
- cli
- parsing
- settings
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


class Arguments:
    """description: 'Owns the protolib CLI argument schema and parser construction.'"""

    def __init__(self, *args, **kwargs):
        """description: 'Build the ArgumentParser with all registered flags.'"""
        self.parser = argparse.ArgumentParser(description="run: python -m protolib info")
        self._add_positional(self.parser, *args, **kwargs)
        self._add_optional(self.parser, *args, **kwargs)

    def __repr__(self, *args, **kwargs) -> str:
        """description: 'Machine-readable representation.'"""
        return "Arguments()"

    def __str__(self, *args, **kwargs) -> str:
        """description: 'Human-readable summary.'"""
        return "Arguments(protolib)"

    def parse(self, *args, **kwargs):
        """description: 'Return parsed argparse.Namespace from sys.argv.'"""
        return self.parser.parse_args()

    def get_required_flags(self, *args, **kwargs) -> dict:
        """description: 'Return a dict mapping each flag/dest to its required status.'"""
        flags = {}
        for action in self.parser._actions:
            if isinstance(action, argparse._StoreAction):
                self._collect_action_flags(*args, action=action, flags=flags, **kwargs)
        return flags

    def _add_positional(self, parser, *args, **kwargs):
        """description: 'Register all positional arguments from _POSITIONAL into the parser.'"""
        for spec in _POSITIONAL:
            parser.add_argument(spec["name"], metavar=spec.get("metavar"), help=spec.get("help"))

    def _add_optional(self, parser, *args, **kwargs):
        """description: 'Register all optional arguments from _OPTIONAL into the parser.'"""
        for spec in _OPTIONAL:
            flags, kw = self._parse_spec(spec, *args, **kwargs)
            parser.add_argument(*flags, **kw)

    def _parse_spec(self, spec: dict, *args, **kwargs) -> tuple:
        """description: 'Convert a flag spec dict into (flags_list, kwargs_dict) for add_argument.'"""
        flags = [k for k in spec if k.startswith("-")]
        long_val = spec.get(flags[0]) if len(flags) == 1 else None
        if long_val:
            flags.append(long_val)
        kw = {k: v for k, v in spec.items() if not k.startswith("-")}
        kw.setdefault("default", None)
        return flags, kw

    def _extract_flag(self, action, *args, **kwargs) -> tuple:
        """description: 'Extract (option_strings, dest, is_required) from a single argparse action.'"""
        is_req = getattr(action, 'required', True) if not action.option_strings \
            else action.required
        return action.option_strings, action.dest, is_req

    def _collect_action_flags(self, *args, action, flags: dict, **kwargs) -> None:
        """description: 'Populate flags dict with option strings (or dest) mapped to required status.'"""
        opts, dest, is_req = self._extract_flag(action, *args, **kwargs)
        for opt in opts:
            flags[opt] = is_req
        if not opts:
            flags[dest] = is_req

def mk_args(*args, **kwargs):
    """description: 'Module-level shim — delegates to Arguments().parse().'"""
    return Arguments(*args, **kwargs).parse(*args, **kwargs)


if __name__ == "__main__":
    a = Arguments()
    ns = a.parse()
    sys.stdout.write(str(a.get_required_flags()) + "\n")
