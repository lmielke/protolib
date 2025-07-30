# entry_point.py
# this is an example api for protopy

from protopy import settings as sts
from protopy.protopy import DefaultClass

def entry_point_function(*args, **kwargs):
    inst = DefaultClass(*args, **kwargs)
    return inst

def main(*args, **kwargs):
    """
    All entry points must contain a main function like main(*args, **kwargs)
    """
    return entry_point_function(*args, pg_name=sts.package_name, **kwargs)