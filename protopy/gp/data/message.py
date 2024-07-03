"""
message.py
##################### protopy Message #####################
manages the messages of the prompt
"""

import json, os, re
from typing import List
from tabulate import tabulate as tb
import protopy.helpers.collections as hlp
import protopy.settings as sts
# message.py
from dataclasses import dataclass, field
from typing import Optional
from protopy.gp.data.content import Content
from datetime import datetime as dt

@dataclass
class Message:
    name: str
    content: Optional[Content] = None
    role: Optional[str] = None
    instructs: Optional[str] = None
    # tag: Optional[str] = None
    watermark: Optional[str] = None
    mType: Optional[str] = None
    mId:str = re.sub(r"([: .])", r"-" , str(dt.now())) + '_Message'
    # use_tags: bool = True

    def __post_init__(self, *args, **kwargs):
        if self.content is None:
            self.content = Content()
            self.content.text = self.content.get_input(f'{self.name}', *args, **kwargs)
        elif not isinstance(self.content, Content):
            self.content = Content(
                                    text=str(self.content), 
                                    instructs=self.instructs, 
                                    tag='expert',
                            )
        if self.role is None:
            self.role = 'input'
        elif self.role == 'assistant':
            self.watermark = sts.watermark if self.watermark is None else self.watermark
        if self.mType is None:
            if self.content is None and self.instructs is not None:
                self.mType = 'instructs'
            else:
                self.mType = 'entry'

    def __str__(self, *args, **kwargs) -> str:
        return self.to_table(*args, **kwargs)

    def to_dict(self, *args, verbose=1, **kwargs) -> dict:
        """Converts the Message instance, including its Content, to a dictionary."""
        # self.set_mid(*args, **kwargs)
        return {
            'name': self.name,
            'content': self.content.construct(*args, **kwargs),
            'role': self.role,
            'watermark': self.watermark,
            'mType': self.mType,
            'mId': self.mId,
        }

    def to_table(self, *args, 
                        tablefmt='plain', use_names:bool=True, use_color:bool=True, **kwargs,
        ) -> None:
        # converts the message to a printable prompt message (using tabulate tables)
        m = self.to_dict(*args, **kwargs)
        name, content = m.get('name'), m.get('content', m.get('text'))
        role, watermark = m.get('role'), m.get('watermark')
        col_name = f"{hlp.color_expert(name, role, watermark)}" if use_color else f"{name}: "
        name = '' if not use_names else col_name
        tbl = [(name, content) if name else (content,)]
        return tb(tbl, tablefmt=tablefmt)
