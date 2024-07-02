"""
tasks.py
##################### protopy Task #####################
manages the tasks to be solved by experts


"""

import json, os, re, subprocess, time
# import for user name
import random as rd
from typing import Literal, Optional, Union

from protopy.gp.experts.experts import Expert
from protopy.gp.data.retrievals import Template
import protopy.helpers.collections as hlp
import protopy.settings as sts


class Task:
    """
    Tasks to be soleved by experts
    """

    def __init__(self, name, assembly_ix:int=None, *args, instructs:str=None, **kwargs ) -> None:
        self.name = name
        self.assembly_ix = assembly_ix if assembly_ix is not None else 1
        # self.sudo = fsts.sudo
        self.instructs = self.load_instructions(*args, **kwargs)
        self.add_experts(*args, **kwargs)

    def load_instructions(self, *args,  context:dict={}, **kwargs):
        """
        Every task requires a different set of instructions for different experts. 
        This function reads the instructions for the expert and returns it.
        """
        context.update({'domain': self.assembly_ix, 'name': self.name})
        self.template = Template(self, *args, t_name=self.name, **kwargs,)
        return self.template.load(context, *args, infos=None, **kwargs,)

    def add_experts(self, expert_names:list=[sts.sudo,], *args, verbose:int=0, **kwargs):
        """
        Every task has to be performed by a set of experts. The experts must have 
        the relevant skill set to collectively solve the task.
        """
        # from all agents sts.sudo must be the first expert to be added
        expert_names = [sts.sudo] + [n for n in expert_names if n != sts.sudo]
        for name in expert_names:
            if name in sts.experts:
                setattr(self, name, sts.experts[name])
            else:
                setattr(self, name, Expert(
                                            name=name, 
                                            instructions=self.instructs,
                                            verbose=verbose,
                                            ))
        return self.get_experts(*args, **kwargs)

    def start(self, *args, **kwargs):
        # every task starts in a determined order
        # experts introduction
        # after the team is introduced, get it started
        self.sudo.chat.add_instructions(
                self.load_instructions(*args, template_type='state', info='project', **kwargs)
                )
        for name, expert in self.get_experts().items():
            expert.ask('Can you quickly introduce yourself?', asker=sts.sudo, verbose=1)
        # after the team is introduced, get it started
        self.sudo.chat.add_instructions(
                            f'Greet your team and give a short summary of the task! '
                            f'Make a suggestion about, how to start!'
                        )
        self.sudo.speak()
        # experts introduction
        for name, expert in self.get_experts().items():
            expert.ask((
                            f'What is the single most important point for you, '
                            f'to consider regarding the feature, to be implemented? '
                            f'Start with: For me as an expert in ...'
                            ), 
                            asker=sts.sudo, volume=1)


    def get_experts(self, *args, **kwargs):
        return {n:e for n, e in self.__dict__.items() if isinstance(e, Expert)}