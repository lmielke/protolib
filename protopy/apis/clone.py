# clone.py
import protopy.settings as sts
from protopy.creator.clone import main as clone
def main(*args, api:str=None, **kwargs) -> None:
    clone(*args, **kwargs)

