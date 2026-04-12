# clone.py
import protolib.settings as sts
from colorama import Fore, Style
from protolib.creator.clone import main as clone


def main(*args, api:str=None, **kwargs) -> None:
    print(f"api.clone: {api = }, {kwargs = }")
    clone(*args, **kwargs)

