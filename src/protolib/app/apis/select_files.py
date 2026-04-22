"""
script_path: src/protolib/app/apis/select_files.py
purpose: CLI wrapper around import_info.select_files.
description: |-
  Parses a target Python file and
  returns the set of source files it imports, enabling dependency-aware workflows.
  Output is JSON-serialised for downstream tooling.
  Usage:
      proto select_files -t <file_path>
      proto select_files -t src/protolib/apis/info.py
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""
import argparse, json, os
from protolib.helpers.import_info import select_files

def set_params(*args, **kwargs) -> dict:
    p = argparse.ArgumentParser(description="Import graph file lister.")
    p.add_argument("-t", "--target", type=str, default=None,
                   help="Python file to trace imports from.")
    p.add_argument("--json", action="store_true", default=False,
                   help="Output full file contents as JSON.")
    return p.parse_args().__dict__

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

def _run_select(*args, path: str, json: bool = False, **kwargs) -> str:
    path = os.path.abspath(path)
    files = select_files(path=path)
    return _print_return(_format_output(files=files, as_json=json, path=path))

def main(*args, tgt_dir=None, target=None, json=False, _cli=False, **kwargs):
    if _cli:
        return main(*args, **set_params())
    path = tgt_dir or target
    if not path:
        return _print_return(_no_target_msg(*args, **kwargs))
    return _run_select(*args, path=path, json=json, **kwargs)


if __name__ == "__main__":
    main(_cli=True)
