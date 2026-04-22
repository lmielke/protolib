"""
script_path: src/protolib/test/app/test_arguments.py
purpose: "Integration tests for app/arguments.py — CLI argument parsing."
update_rules: "Append scenarios. Never remove existing tests."
"""
import unittest
from protolib.app.arguments import (
    _POSITIONAL, _OPTIONAL, _parse_spec, _add_positional, _add_optional,
)
import argparse


class TestParseSpec(unittest.TestCase):
    """_parse_spec: extract flags and kwargs from spec dict."""

    def test_short_and_long_flag(self, *args, **kwargs):
        spec = {"-v": "--verbose", "type": int, "help": "verbosity"}
        flags, kw = _parse_spec(spec)
        assert "-v" in flags
        assert "--verbose" in flags
        assert kw["type"] is int

    def test_long_only_flag(self, *args, **kwargs):
        spec = {"--port": None, "type": str, "help": "port"}
        flags, kw = _parse_spec(spec)
        assert "--port" in flags
        assert len(flags) == 1

    def test_default_none(self, *args, **kwargs):
        spec = {"--test": None, "type": str, "help": "x"}
        _, kw = _parse_spec(spec)
        assert kw["default"] is None


class TestArgDefinitions(unittest.TestCase):
    """_POSITIONAL / _OPTIONAL: argument definitions are well-formed."""

    def test_positional_has_api(self, *args, **kwargs):
        names = [p["name"] for p in _POSITIONAL]
        assert "api" in names

    def test_optional_has_verbose(self, *args, **kwargs):
        has_verbose = any("-v" in spec for spec in _OPTIONAL)
        assert has_verbose

    def test_all_optional_have_help(self, *args, **kwargs):
        for spec in _OPTIONAL:
            assert "help" in spec, f"Missing help in {spec}"


class TestAddArguments(unittest.TestCase):
    """_add_positional / _add_optional: add args to parser."""

    def test_adds_positional(self, *args, **kwargs):
        p = argparse.ArgumentParser()
        _add_positional(p)
        actions = {a.dest for a in p._actions}
        assert "api" in actions

    def test_adds_optional(self, *args, **kwargs):
        p = argparse.ArgumentParser()
        _add_optional(p)
        dests = {a.dest for a in p._actions}
        assert "verbose" in dests
        assert "port" in dests


if __name__ == '__main__':
    unittest.main()
