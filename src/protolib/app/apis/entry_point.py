"""
script_path: src/protolib/app/apis/entry_point.py
description: >-
  Template entry point for protolib and cloned packages. EntryPoint wraps DefaultClass,
  injecting the package name from settings. Clone this file and override EntryPoint.run()
  to customise the execution sequence for a new package.
tags:
- blueprint
- cli
- settings
"""

import protolib.app.settings as sts
from protolib.app.protopy import DefaultClass


class EntryPoint:
    """description: 'Thin CLI adapter — owns DefaultClass creation with package name injected.'"""

    def __init__(self, *args, **kwargs):
        """description: 'Instantiate DefaultClass, forwarding all arguments.'"""
        self.instance = DefaultClass(*args, **kwargs)

    def run(self, *args, **kwargs):
        """description: 'Return the wrapped DefaultClass instance.'"""
        return self.instance

    def __repr__(self) -> str:
        """description: 'Machine-readable representation showing wrapped instance.'"""
        return f"EntryPoint(instance={self.instance!r})"

    def __str__(self) -> str:
        """description: 'Human-readable summary of the wrapped instance.'"""
        return f"EntryPoint({self.instance})"

def main(*args, **kwargs):
    """description: 'All entry points must contain a main(*args, **kwargs) function.'"""
    return EntryPoint(*args, pg_name=sts.package_name, **kwargs).run()


if __name__ == '__main__':
    main()
