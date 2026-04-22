"""
script_path: src/protolib/app/apis/entry_point.py
purpose: >-
  Example API entry point that demonstrates how to wire a new API into the protolib
  dispatch system.
description: |-
  Instantiates DefaultClass and forwards all kwargs
  transparently. Clone this file and rename when adding application APIs.
governance_exceptions:
  - c8: "no class definition — verify OOP intent"
"""

import protolib.app.settings as sts
from protolib.app.protopy import DefaultClass

def entry_point_function(*args, **kwargs):
    inst = DefaultClass(*args, **kwargs)
    return inst

def main(*args, **kwargs):
    """
    purpose: All entry points must contain a main function like main(*args, **kwargs)
    """
    return entry_point_function(*args, pg_name=sts.package_name, **kwargs)
if __name__ == '__main__':
    main()
