# get_creds.py
import os, sys
from getpass import getpass as gp
import colorama as color

color.init()


class Creds:
    def __init__(self, *args, **kwargs):
        self.rules = None  # implement key rules here

    def set(self, msg="key", *args, force=True, confirmed=True, key=None, **kwargs):
        key = self.get(key, *args, **kwargs)
        if not key:
            key = None
            while not key:
                key = gp(prompt=f"{msg.strip(': ')}: ", stream=None)
                if force == False:
                    break
            while not confirmed:
                confirmed = self._confirm_equals(key, *args, **kwargs)
        key = self.get(key, *args, **kwargs)
        return key

    def get(self, key, *args, safeName=None, **kwargs):
        if key == "os":
            msg = f"\tUsing $env:key {safeName}"
            key = os.environ["DATASAFEKEY"]
            print(f"{color.Fore.YELLOW}{msg}{color.Style.RESET_ALL}")
        return key

    def _confirm_equals(self, key, *args, **kwargs):
        # getting new key
        confirmKey = None
        while confirmKey != key:
            confirmKey = gp(prompt=f"re-type key to continue: ", stream=None)
        return True
