import argparse
import os
from typing import Dict
import protopy.settings as sts


class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        if "the following arguments are required: api" in message:
            available_apis = self.get_available_apis()
            available_apis_message = "\nAvailable APIs:\n" + "\n".join(available_apis)
            self.exit(2, f"{self.prog}: error: {message}\n{available_apis_message}\n")
        else:
            super().error(message)

    @staticmethod
    def get_available_apis():
        try:
            apis = [os.path.splitext(p)[0] for p in os.listdir(sts.apis_dir) \
                                                if p.endswith('.py') and p != '__init__.py']
        except FileNotFoundError:
            apis = ["<API directory not found>"]
        return [', '.join(apis)]


def mk_args():
    parser = CustomArgumentParser(description="run: python -m protopy info")
    parser.add_argument(
        "api",
        metavar="api",
        nargs=None,
        help=f"{CustomArgumentParser.get_available_apis()}",
    )

    parser.add_argument(
        "-pr",
        "--new_pr_name",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=[],
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
        help="python version placed inside your Pipfile.",
    )

    parser.add_argument(
        "-e",
        "--experts",
        required=False,
        nargs="+",
        const=None,
        type=str,
        default=None,
        help="Names of experts you intend to use. Default: None",
    )

    parser.add_argument(
        "-k",
        "--skills",
        required=False,
        nargs="+",
        const=None,
        type=str,
        default=None,
        help="Names of skills you intend to use in addition to expert sills. Default: None",
    )

    parser.add_argument(
        "-q",
        "--question",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help="Question for the single short prompt.",
    )

    parser.add_argument(
        "-f",
        "--function",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default='none',
        help="States if functions should be used ['auto', str(function_name)] or not. 'none'",
    )

    parser.add_argument(
        "-m",
        "--model",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help="Names of model you intend to use. Default: gpt-3.5-turbo-0125",
    )

    parser.add_argument(
        "-r",
        "--regex",
        required=False,
        nargs=None,
        const=None,
        type=str,
        default=None,
        help="Names of file for file based operations.",
    )

    parser.add_argument(
        "--install",
        required=False,
        nargs="?",
        const=1,
        type=bool,
        default=None,
        help="This will trigger pipenv to install the environment using py_version.",
    )

    parser.add_argument(
        "-s",
        "--show",
        required=False,
        nargs="?",
        const=1,
        type=bool,
        default=False,
        help="Triggers the result to be shown as a digraph is possible.",
    )

    parser.add_argument(
        "-i",
        "--infos",
        required=False,
        nargs="+",
        const=None,
        type=str,
        default=None,
        help="list of infos to be retrieved, default: all",
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
            is_required = getattr(action, 'required', True) \
                if action.option_strings == [] else action.required
            # Option strings is a list of option strings (e.g., '-f', '--foo').
            for option_string in action.option_strings:
                required_flags[option_string] = is_required
            if not action.option_strings:  # For positional arguments
                required_flags[action.dest] = is_required
    return required_flags


if __name__ == "__main__":
    args = mk_args()
    required_flags = get_required_flags(args)
    print(required_flags)
