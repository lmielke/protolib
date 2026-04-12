"""
    Entry point for protolib shell calls
    ###################################################################################

    __main__.py imports the api module from protolib.apis >> apiModule.py
                and runs it
                api is provided as first positional argument

    ###################################################################################

    for user info runs:
        python -m protolib info
    above cmd is identical to
        python -m protolib.apis.info


"""

import colorama as color

color.init()
import importlib

import protolib.settings as sts
import protolib.arguments as arguments
import protolib.contracts as contracts


def runable(*args, api, **kwargs):
    """
    imports api as a package and executes it
    returns the runable result
    """
    return importlib.import_module(f"protolib.apis.{api}")


def main(*args, **kwargs):
    """
    to runable from shell these arguments are passed in
    runs api if legidemit and prints outputs
    """
    kwargs = arguments.mk_args().__dict__

    # kwargs are vakidated against enforced contract
    kwargs = contracts.checks(*args, **kwargs)
    if kwargs.get("api") != "help":
        runable(*args, **kwargs).main(*args, **kwargs)


if __name__ == "__main__":
    main()
