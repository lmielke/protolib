"""
expert.py
##################### protopy Prompt #####################
do whatever you imagine


"""

import json, os, re, subprocess, time
from tabulate import tabulate as tb
# import for user name
import random as rd
from typing import Literal, Optional, Union
import protopy.helpers.collections as hlp
import protopy.settings as sts
from protopy.gp.data.chat import Chat
from protopy.gp.data.retrievals import Template


class Expert:
    """
    Generates experts to be added to a OpenAI expert object
    This holds only the message dictionary with the fields listed in self.fields
    """

    def __init__(self, *args, name:str=sts.sudo, role:str=None, d_assi:str=None, **kwargs ) -> None:
        # assistant message fields like self.fields
        # expert with same name must not exist
        self.color_code, self.color = self.set_color(name, *args, **kwargs)
        self.name, self.name_regex = name.lower(), self.set_name_regex(name, self.color)
        self.role = role if role is not None else 'assistant'
        self.domain, self.d_assi, self.kxs, self.infos = self.get_info_names(*args, **kwargs)
        self.last_said, self.last_heared, self.respondent = None, None, None
        self.instructs = self.load_instructions(*args, **kwargs)
        # the master chat relates to the task to be performed
        self.create_chat('master', *args, **kwargs)
        self.add_expert_to_mixture(*args, **kwargs)

    def __str__(self, *args, **kwargs):
        # we return all paramterts that are not classes or methods
        params = {k: v for k, v in self.__dict__.items() if not hasattr(v, '__dict__')}
        del params['color_code']
        del params['instructs']
        params['chats'] = list(params['chats'].keys())
        params = tb(params.items(), headers=['Parameter', 'Value'], tablefmt='grid')
        return f"\nExpert({self.name}, {self.role}): \n{params}"

    def create_chat(self, chat_name, *args, instructs:str='', **kwargs):
        """
        Each expert can have multiple chats with different names of which one is the 'master'.
        The master chat is the main chat for the expert and is used to communicate
        with other experts.
        """
        if not hasattr(self, 'chats'): self.chats = {}
        # every known expert type has pre defined instructions to be added here
        self.chats[chat_name] = Chat(   owner=self,
                                        use_tags = kwargs.get('use_tags'),
                                        use_names = kwargs.get('use_names'),
                                )
        # after chat is created append additional instructions
        self.chats[chat_name].initialize(   instructs if instructs else self.instructs, *args,
                                            tag=self.name, 
                                            infos=self.infos,
                                            **kwargs
                            )

    def add_expert_to_mixture(self, *args, **kwargs):
        # assert len(sts.experts) < sts.max_experts, f"Max num experts: {sts.max_experts}!"
        assert self.name not in sts.experts, f"Expert with name {self.name} already exists."
        sts.experts[self.name] = self

    def get_info_names(self, *args, **kwargs):
        domain, d_assi, kxs, info = list(sts.skills.get(
                                                self.name, 
                                                sts.skills.get(sts.default_expert)).values()
                                )
        return domain, d_assi, kxs, info

    def get_experts_infos(self, *args, **kwargs):
        expert_infos = '###Available experts: \n'
        for expert in sts.experts.values():
            expert_infos += (f"- {expert.name.capitalize()}: "
                                f"Domain: {expert.domain}, "
                                f"knows: {expert.infos}\n"
                                )
        return expert_infos

    def load_instructions(self, context:dict={}, *args, infos:list=None, instructs:str=None, **kwargs):
        """
        Every task requires a different set of instructs for different experts. 
        This function reads the instructs for the expert and returns it.
        """
        # some parts of instructs can be read from the OS using 'proto info'
        # sts.skills defines some skills depending on the name of the expert
        instructs = '' if instructs is None else instructs
        infos = list(set(self.infos if infos is None else infos))
        self.template = Template(self, *args, t_name=self.domain, **kwargs,)
        context.update({'domain': self.domain, 'name': self.name})
        instructs += self.template.load(context, *args, infos=infos, **kwargs,)
        return instructs

    def set_color(self, name, *args, color:str=None, **kwargs):
        """
        Dynamically get the color attribute from the sts module based on the color name
        """
        if color and color.upper() in sts.colors_available:
            # check if color is available in sts module
            color_code = getattr(sts, color.upper(), None)
        elif name == sts.sudo:
            color, color_code = sts.sudo_color, sts.sudo_color_code
        else:
            # assin a random color from sts module
            try:
                color = rd.choice(list(sts.colors_available))
            except IndexError as e:
                color = sts.default_color
            color_code = getattr(sts, color, None)
        if color.upper() in sts.colors_available:
            sts.colors_available.remove(color.upper())
        return color_code, color

    def set_name_regex(self, name, color, *args, **kwargs):
        """
        Sometimes the agent response contains the colored name of the chat participant, 
        and sometimes it does sometimes not. If the response starts with the name,
        it is removed from Content.text instance. The possible name appearences are kept
        in the names list. Here we construct the regex to find instances of that case.
        # example colored name: \x1b[32mut_expert\x1b[39m
        """
        return (
                f"^{self.color_code}{name}:?{sts.RESET}|"
                f"^{self.color_code}{name}:?{sts.ST_RESET}|"
                f"^{name}:?"
                )


    def _think(self, message=None, *args, role:str=None, instructs:str=None, **kwargs):
        """
        generates a new message (thought) to be added to the discussion. Note, a thought
        is a message that is not yet spoken. Therefore its only appended to self.chat
        """
        role = role if role is not None else self.role
        # case 2 thought is not provided then think about it
        self.chats['master'].add_instructions(instructs, *args, **kwargs)
        if message is None and role == 'assistant':
            self.chats['master'].get_model_response(*args, to_chat=True, **kwargs)
        # if non of the conditions above apply, trigger manual input via content=None
        else:
            self.chats['master'].append(message, *args, instructs=instructs, role=role, **kwargs)
        return self.chats['master'].messages[-1]

    def speak(self, message=None, *args, to:[set, None, False]=sts.experts.keys(), **kwargs):
        """
        Adds the current thought or spoken message to all experts' chats except the sender.

        This function allows the expert to communicate with other experts by sharing 
        the generated thought/message. If the 'to' parameter is set to None/False, 
        the message is only added to the sender's chat.

        Args:
            message (str, optional): The message to be thought and spoken.
            to (set, None, False, optional): Specifies the recipients of the message.
                - If set to a set of expert names, the message is sent to those experts.
                - If set to None or False, the message is only added to the sender's chat.
                - If not provided, the message is sent to all experts except the sender.
            *args: Additional arguments for message processing.
            **kwargs: Additional keyword arguments for message processing.

        Returns:
            Message: The generated thought/message.
        """
        thought = self._think(message, *args, **kwargs)
        # if None was provided as to, then only the agent gets the message
        if not to:
            return thought
        # all recipients get the message except the sender
        for recipient in {expert for expert in sts.experts.values() if expert.name in to}:
            if recipient.name != self.name:
                recipient.listen(thought, *args, **kwargs)
        self.last_said = thought
        return thought

    def ask(self,   respondent_name:str, question:str=None, *args, 
                    instructs:str=None, role:str=None, use_names:bool=True, **kwargs):
        """
        Generates a question (message) and appends it to the chat
        Then lets the agent speak, to ask that question.
        """
        # get the respondent_name instance from sts.experts
        respondent = sts.experts.get(respondent_name, None)
        # this is asking the question
        name_prefix = f"@{respondent.name} " if use_names else ''
        question = f"{name_prefix} Question: {question}" if question is not None else None
        self.speak(question, *args, role='user', **kwargs)
        # this is requesting the answer from expert the quesion was asked to
        return respondent.speak(None, *args, role='assistant', instructs=instructs, **kwargs)

    def answer(self, asker_name:str, question:str=None, *args,
                    instructs:str=None, role:str=None, **kwargs):
        """
        Convenience method that lets the agent answer the question asked by another agent. 
        Uses self.ask with reversed roles for asker and respondent.
        """
        asker = sts.experts.get(asker_name, None)
        return asker.ask(self.name, question, *args, instructs=instructs, **kwargs)

    def listen(self, text:str=None, *args, instructs:str=None, **kwargs):
        """
        Listens to a given message and adds it to its own chat (as text or instrcts)
        Note: this is not added to any other experts chat
        """
        if text is not None:
            thought = self._think(text, *args, instructs=instructs, **kwargs)
            self.last_heared = thought
        elif instructs is not None:
            if sts.experts.get(sts.sudo) is not None and self.name != sts.sudo:
                sts.experts[sts.sudo].listen(text=instructs)
