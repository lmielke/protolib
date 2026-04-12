# select_files.py
"""
CLI wrapper around import_info.select_files.

Usage:
    proto select_files -t <file_path>
    proto select_files -t src/protolib/apis/info.py
"""
import argparse
import json
import os


def set_params(*args, **kwargs) -> dict:
    parser = argparse.ArgumentParser(
        description="List files reachable via import graph from a given file."
    )
    parser.add_argument(
        "-t", "--target",
        type=str,
        default=None,
        help="Path to the Python file to trace imports from (default: cwd).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output full file contents as JSON instead of a plain path list.",
    )
    return parser.parse_args().__dict__


def main(*args, **kwargs):
    if not kwargs:
        kwargs = set_params(*args, **kwargs)

    from protolib.helpers.import_info import select_files

    path = kwargs.get("tgt_dir") or kwargs.get("target")
    if not path:
        output = (
            "select_files: no target provided.\n"
            "Usage: /select_files/?target=src/protolib/apis/info.py\n"
            "Returns files reachable via import graph from the given file."
        )
        print(output)
        return output

    path = os.path.abspath(path)
    files = select_files(path=path)

    if not files:
        output = f"select_files: no files found for target '{path}'."
    elif kwargs.get("json"):
        output = json.dumps(files, indent=2)
    else:
        output = "\n".join(entry["file_path"] for entry in files)

    print(output)
    return output


if __name__ == "__main__":
    main()
