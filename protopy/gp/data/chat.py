# chat.py

import json, os, pickle, re
from datetime import datetime as dt
from tabulate import tabulate as tb
from dataclasses import dataclass, field, InitVar
from typing import Optional, ClassVar, List, Tuple
from protopy.gp.data.content import Content
from protopy.gp.data.message import Message
from protopy.gp.data.retrievals import Template
from protopy.gp.models.openai.prompt import Prompt
from protopy.gp.data.infosys import InfoSys

# from protopy.gp.data.instructions import Instructions
import protopy.settings as sts
import protopy.helpers.collections as hlp

@dataclass
class Chat:
    owner: object
    chat_type: Optional[str] = 'simple chat'
    instructs: Optional[str] = ''
    # infos: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    use_tags: bool = True # controlls if the tags are shown in the chat instructions
    use_names: bool = True # controlls if the names of the experts are shown in the chat
    chId:str = re.sub(r"([: .])", r"-" , str(dt.now()))
    chType:str = '_Chat'

    def __post_init__(self, *args, **kwargs) -> None:
        # self.readme = self.load_readme()
        pass

    def initialize(self, *args, **kwargs):
        d_assi = self.owner.__dict__.get('d_assi', None)
        self.prompt = Prompt(self, *args, d_assi=d_assi, **kwargs)
        self.load_instructions(*args, **kwargs)
        self.load_infos(*args, **kwargs)
        sts.in_chat.add(self.owner.name)


    def create_t_name(self, *args, **kwargs) -> str:
        t_name = []
        if self.use_tags:
            t_name.append('use_tags')
        if self.use_names:
            t_name.append('use_names')
        return '_'.join(t_name)

    def load_instructions(self, *args, **kwargs):
        """
        Every task requires a different set of instructs for different experts. 
        This function reads the instructs for the expert and returns it.
        """
        # infos are handled latter
        if 'infos' in kwargs: del kwargs['infos']
        if 'tgt_dir' in kwargs: del kwargs['tgt_dir']
        t_name = self.create_t_name(*args, **kwargs)
        tag_examples = '\n- '.join([f"{k}:{vs}" for k, vs in sts.tags.items() 
                                                                if k in ['chat', 'expert']])
        context = {'chat_type': self.chat_type, 'in_chat': sts.in_chat, 'tags': tag_examples}
        self.template = Template(self, *args, t_name=t_name, **kwargs,)
        # adds Chat specific context to the template context
        self.instructs += '\n' + self.template.load(context, *args, **kwargs)
        self.add_instructions(  self.instructs, *args, 
                                mType=f"instructs{self.chType}", 
                                **kwargs,
        )

    def load_infos(self, *args, **kwargs):
        """
        Every task requires a different set of instructs for different experts. 
        This function reads the instructs for the expert and returns it.
        """
        self.template = Template(InfoSys(self), *args, t_name='', **kwargs,)
        info_text = self.template.load({}, *args, **kwargs)
        # adds Chat specific context to the template context
        self.add_instructions(info_text, *args, mType=f"infos{self.chType}", **kwargs)

    def get_model_response(self, *args, role:str='assistant', to_chat:bool=True, **kwargs):
        self.prompt(*args, **kwargs)
        message = Message(
                            name=self.owner.name, 
                            role=role, 
                            mId=self.chId,
                            mType='assi_response',
                            **self._organize(*args, **kwargs))
        if to_chat: self.append(message, *args, **kwargs)
        return message

    def add_instructions(self,  instructs, *args, 
                                tag='chat', mId:str=None, mType:str=None, **kwargs
        ) -> Message:
        """
        Adds chat instructions to the chat.
        """
        if not instructs: return None
        self.messages.append(Message(
                                    name=sts.sudo, # instructions are only given by sudo
                                    content=Content(text='', tag=tag, instructs=instructs),
                                    role='system', # role is 'system' for instructions
                                    mId=mId,
                                    mType=mType,
                            )
        )

        return self.messages[-1]

    def append(self, message: [Message, str, None], *args, role:str=None, **kwargs) -> None:
        """Appends a message to the chat."""
        if not isinstance(message, Message):
            message = Message(
                                name=self.owner.name,
                                content=message,
                                role=role if role is not None else self.owner.role,
                                )
        self.messages.append(message)
        return self.messages[-1]

    def remove(self, mId:str, *args, **kwargs) -> None:
        """Gets the last message from messages and sets content to 'post removed'."""
        for m in self.messages:
            if m.mId == mId:
                m.mType = 'removed'

    def __str__(self, *args, **kwargs) -> str:
        """String representation of the chat, showing all messages."""
        os.system('cls' if os.name == 'nt' else 'clear')
        return self.to_table(*args, **kwargs)

    def to_table(self, *args, tablefmt:str='grid', **kwargs) -> List[dict]:
        """Converts the Chat instance, including all its Messages, to a list of dictionaries."""
        msgs = []
        for i, (name, message) in enumerate(self.to_chat(*args, **kwargs)):
            if self.owner.name == sts.sudo and i == 0:
                message += sts.experts[self.owner.name].get_experts_infos(*args, **kwargs)
            msgs.append((message, ))
        headers = [
                    (   f'{sts.YELLOW}Chat for expert {self.owner.name[:20].upper()}{sts.RESET}'
                        f' with {len(self.messages)} entries.'), 
                        'MESSAGE']
        return tb(msgs, headers=headers, tablefmt=tablefmt)

    def to_chat(self, *args, tablefmt:str='plain', **kwargs) -> None:
        """Converts the chat to a printable format using tabulate tables.
            tablefmt: str We are pulling tablefmt out here to avoide multiple values
        """
        # converts the message to a printable prompt message (using tabulate tables)
        msgs = []
        for message in self.messages:
            msgs.append([
                message.name, 
                message.to_table(*args, use_names=self.use_names, **kwargs)
                ])
        return msgs

    def to_dict(self, *args, **kwargs) -> dict:
        msgs = {}
        for i, message in enumerate(self.messages):
            msgs[i] = message.to_dict(*args, **kwargs)
        return msgs

    def save_chat(self, chat_hist_dir:str=sts.chat_hist_dir, chat_name:str=None) -> None:
        """
        Serializes the Chat instance to a file using pickle.

        Args:
            chat_hist_dir (str): The path to the file where the chat will be saved.
        """
        chat_name = self.owner.name if chat_name is None else chat_name
        file_name = f"{sts.session_id}_{chat_name}"
        __dict__, self.__dict__ = self.__dict__, self._get_picklable_copy()
        with open(os.path.join(chat_hist_dir, file_name), 'wb') as f:
            pickle.dump(self, f)
        self.__dict__ = __dict__


    def _get_picklable_copy(self):
        """
        Returns a picklable copy of the Chat instance by removing or replacing
        unpicklable attributes.
        """
        chat_copy = self.__dict__.copy()
        for key, value in chat_copy.items():
            try:
                # Attempt to pickle the value to test if it's picklable
                pickle.dumps(value)
            except (pickle.PicklingError, TypeError, AttributeError):
                chat_copy[key] = None  # Replace unpicklable attributes with None or appropriate default
        return chat_copy


    def load_chat(self, chat_hist_dir:str=sts.chat_hist_dir, chat_name:str=None) -> 'Chat':
        """
        Deserializes the Chat instance from a file using pickle.

        Args:
            chat_hist_dir (str): The path to the file from which the chat will be loaded.

        Returns:
            Chat: The deserialized Chat instance.
        """
        # if no chat_name is provided the most recent chat from the owner is picked
        if chat_name is None:
            chats = [c for c in os.listdir(chat_hist_dir) if self.owner.name in c]
        elif chat_name:
            chats = [c for c in os.listdir(chat_hist_dir) if chat_name in c]
        file_name = sorted(chats)[-1]
        with open(os.path.join(chat_hist_dir, file_name), 'rb') as f:
            return pickle.load(f)
    
    def _organize(self, *args, **kwargs):
        if self.prompt.response.function.func_response:
            instructs = (
                            f"Function execution requested: {self.prompt.function.name} ,"
                            f"Requested by: {self.name.capitalize()} \n"
                            f"- name: {self.prompt.function.name}\n"
                            f"- arguments: {self.prompt.function.arguments}\n"
                            f"- executor: {self.color_code}{self.name}{sts.RESET}\n"
                            )
            content = self.prompt.response.content
            content = content.strip() if content is not None else '...'
            watermark = sts.exec_watermark
        else:
            content, instructs = self.prompt.response.content.strip(), None
            watermark = sts.watermark
        return {'content': content, 'instructs': instructs, 'watermark': watermark, }

    def execute(self, *args, **kwargs):
        self.exe_out = {}
        if self.prompt.function.func_response and self.prompt.function.is_safe:
            self.exe_out = self.prompt.function.execute()
            self.listen(self.exe_out.get('body'), f"{self.exe_out}")
            sts.experts.get(sts.sudo, self).listen(self.exe_out['body'])
        else:
            self.exe_out = {'status': None, 'body': None}
