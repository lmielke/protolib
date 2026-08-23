"""
script_path: src/protolib/app/apis/select_files.py
description: >-
  Wraps the import_info.select_files helper to list source files reachable via the import
  graph from a target Python file. Accepts a target path and optional JSON flag, then prints
  the resolved file list or serialized contents. Serves as the CLI entry point for the proto
  select_files command, consumed by downstream tooling that needs dependency-aware file selection.
tags:
- cli
- infra
- parsing
"""
import argparse, json, os
from protolib.helpers.import_info import select_files as _get_files


class SelectFiles:
    """description: 'Resolves and formats import-graph file lists for CLI output.'"""

    def __init__(self, *args, path: str = None, as_json: bool = False, **kwargs):
        """description: 'Store resolved path and output format flag.'"""
        self.path = os.path.abspath(path) if path else None
        self.as_json = as_json

    def run(self, *args, **kwargs) -> str:
        """description: 'Resolve files via import graph and return formatted output string.'"""
        if not self.path:
            return _print_return(_no_target_msg(*args, **kwargs), *args, **kwargs)
        files = _get_files(path=self.path)
        return _print_return(_format_output(*args, files=files, as_json=self.as_json,
                                           path=self.path, **kwargs), *args, **kwargs)

    def __repr__(self) -> str:
        return f"SelectFiles(path={self.path!r}, as_json={self.as_json!r})"

    def __str__(self) -> str:
        return f"SelectFiles({self.path or 'no target'}, json={self.as_json})"

def _no_target_msg(*args, **kwargs) -> str:
    return ("select_files: no target provided.\n"
            "Usage: /select_files/?target=src/protolib/apis/info.py\n"
            "Returns files reachable via import graph from the given file.")

def _format_output(*args, files: list, as_json: bool = False, path: str = "", **kwargs) -> str:
    if not files:
        return f"select_files: no files found for target '{path}'."
    if as_json:
        return json.dumps(files, indent=2)
    return "\n".join(entry["file_path"] for entry in files)

def _print_return(msg: str, *args, **kwargs) -> str:
    print(msg)
    return msg

def set_params(*args, **kwargs) -> dict:
    p = argparse.ArgumentParser(description="Import graph file lister.")
    p.add_argument("-t", "--target", type=str, default=None,
                   help="Python file to trace imports from.")
    p.add_argument("--json", action="store_true", default=False,
                   help="Output full file contents as JSON.")
    return p.parse_args().__dict__

def main(*args, tgt_dir=None, target=None, _cli=False, json: bool = False, **kwargs):
    """description: 'CLI shim — parse args or forward kwargs to SelectFiles.run.'"""
    if _cli:
        return main(*args, **set_params(*args, **kwargs), **kwargs)
    path = tgt_dir or target
    return SelectFiles(*args, path=path, as_json=json, **kwargs).run(*args, **kwargs)


if __name__ == "__main__":
    main(_cli=True)
