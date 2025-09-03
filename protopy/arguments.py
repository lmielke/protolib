"""
    pararses protopy arguments and keyword arguments
    args are provided by a function call to mk_args()
    
    RUN like:
    import protopy.arguments
    kwargs.updeate(arguments.mk_args().__dict__)
"""
import argparse
from typing import Dict


def mk_args():
    parser = argparse.ArgumentParser(description="run: python -m protopy info")
    parser.add_argument(
                            "api", 
                            metavar="api", nargs=None, 
                            help=(
                                    f""
                                    f"see protopy.apis"
                                )
                        )

    parser.add_argument(
        "-pr",
        "--new_pr_name",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help="project name (top folder) default parameter to change",
    )

    parser.add_argument(
        "-n",
        "--new_pg_name",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help="default parameter to change",
    )

    parser.add_argument(
        "-a",
        "--new_alias",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help="alias you call the future package with, if left blank new_pg_name[:6] is used",
    )

    parser.add_argument(
        "-t",
        "--tgt_dir",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help="default parameter to change",
    )

    parser.add_argument(
        "-p",
        "--py_version",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help=f"python version placed inside your Pipfile.",
    )

    parser.add_argument(
        "--port",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help=f"Port to run server.pyw on i.e. 9005"
    )

    parser.add_argument(
        "-m",
        "--model",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help=(f"Names of model you intend to use. Default: gpt-3.5-turbo-0125"),
    )

    parser.add_argument(
        "--install",
        required=False,
        nargs="?",
        const=1,
        type=bool,
        default=None,
        help=f"This will trigger pipenv to install the environment using py_version.",
    )

    parser.add_argument(
        "-i",
        "--infos",
        required=False,
        nargs="+",
        const=None,
        type=str,
        default=None,
        help="list of infos to be retreived, default: all",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        required=False,
        nargs="?",
        const=1,
        type=int,
        default=0,
        help="0:silent, 1:user, 2:debug",
    )

    parser.add_argument(
        "-y",
        "--yes",
        required=False,
        nargs="?",
        const=1,
        type=bool,
        default=None,
        help="run without confirm, not used",
    )

    return parser.parse_args()



def get_required_flags(parser: argparse.ArgumentParser) -> Dict[str, bool]:
    """
    Extracts the 'required' flag for each argument from an argparse.ArgumentParser object.

    Args:
        parser (argparse.ArgumentParser): The parser to extract required flags from.

    Returns:
        Dict[str, bool]: A dictionary with argument names as keys and their 'required' status as values.
    """
    required_flags = {}
    for action in parser._actions:
        if isinstance(action, argparse._StoreAction):
            # For positional arguments, the 'required' attribute is not explicitly set,
            # but they are required by default.
            is_required = getattr(action, 'required', True) if action.option_strings == [] else action.required
            # Option strings is a list of option strings (e.g., '-f', '--foo').
            for option_string in action.option_strings:
                required_flags[option_string] = is_required
            if not action.option_strings: # For positional arguments
                required_flags[action.dest] = is_required
    return required_flags

if __name__ == "__main__":
    parser = mk_args()
    required_flags = get_required_flags(parser)
    print(required_flags)
