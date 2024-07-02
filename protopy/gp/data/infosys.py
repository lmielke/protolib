"""
infosys.py
"""
from dataclasses import dataclass, field, InitVar

import protopy.settings as sts
import protopy.helpers.collections as hlp

@dataclass
class InfoSys:
    owner: object

    def __post_init__(self, *args, **kwargs) -> None:
        pass