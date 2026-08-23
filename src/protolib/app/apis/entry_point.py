"""
script_path: src/protolib/app/apis/entry_point.py
description: >-
  Serves as a template for wiring new APIs into the protolib dispatch system. Instantiates
  DefaultClass and forwards all arguments transparently. Injects the package name from settings
  before returning the instance. Developers clone this file to create new application entry
  points.
tags:
- blueprint
- cli
- settings
governance_exceptions:
- c8: no class definition — verify OOP intent
"""

import protolib.app.settings as sts
from protolib.app.protopy import DefaultClass

def entry_point_function(*args, **kwargs):
    inst = DefaultClass(*args, **kwargs)
    return inst

def main(*args, **kwargs):
    """
    description: All entry points must contain a main function like main(*args, **kwargs)
    """
    return entry_point_function(*args, pg_name=sts.package_name, **kwargs)
if __name__ == '__main__':
    main()
