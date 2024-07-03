"""
prompt.py
##################### protopy Prompt #####################
creates chat structure


"""


import getpass, json, os, re, requests, subprocess, time, yaml
from datetime import datetime as dt
from tabulate import tabulate as tb
from functools import wraps
from openai import OpenAI
from typing import List

import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.apis.info import main as info
from protopy.gp.models.openai.funcs import Function
from protopy.gp.data.texts import Text
import protopy.gp.models.openai.model_settings as gp_sts



class Prompt:
    
    def __init__(self, owner:object, *args, d_assi:str=None, **kwargs ) -> None:
        self.owner = owner
        self.response = Response(*args, **kwargs)
        # prompt uses default model using __call__, or a specifc model using mk_prompt()
        self.d_assi = d_assi if d_assi is not None else self.owner.d_assi if hasattr(self.owner, 'd_assi') else None
        self.assi = Assistant(*args, d_assi=self.d_assi, **kwargs)
        self.context = {}
        self.msg = lambda role, content: {'role': role, 'content': content}

    def __call__(self, *args, **kwargs):
        self.mk_prompt(*args, **kwargs)
        self.to_table(*args, **kwargs)
        self.response(self.assi.post(self.context, *args, **kwargs), *args, **kwargs )
        return self.response.__dict__

    def to_table(self, *args, verbose:int=0, **kwargs):
        if verbose:
            t = [m.values() for m in self.context['messages']]
            tbl = tb(t, headers=['role', 'content'])
            print(f"Prompt.to_table: \n{tbl}")

    def mk_prompt(self, *args, model:str=None, tmp:float=None, **kwargs):
        """
        Creates a prompt using the OpenAI API and sends it to the OpenAI API.
        Model and temperature (tmp) can be set here or are taken from prompt instance.
        """
        self.context['temperature'] = self.assi.temperature if tmp is None else tmp
        self.context['model'] = self.assi.model
        self.context['messages'] = self.prep_messages(*args, **kwargs)
        self.add_tools(*args, **kwargs)

    def prep_messages(self, *args, verbose:int=0, single_shot:bool=False, **kwargs):
        M, q_role, start = [], None, True
        for vs in self.owner.to_dict(*args, **kwargs).values():
            for n, v in vs.items():
                if n == 'role':
                    role = gp_sts.add_tags(self.assi.tag, v, n)
                    if start:
                        role = gp_sts.add_tags(self.assi.tag, role, 'start')
                elif n == 'content':
                    content = gp_sts.add_tags(self.assi.tag, v, n)
            M.append( self.msg(role, content) )
            q_role = role
        M.append( self.msg('<|start_header_id|>assistant<|end_header_id|>', ''))
        if single_shot:
            content = tb([[msg.get('content')] for msg in M])
            M = [ {'role': q_role, 'content': content}, ]
            if verbose:
                print(f"{sts.YELLOW}\nPrompt.prep_messages: Single shot!{sts.RESET}\n{content}")
        return M

    def add_tools(self, *args, function:str='none', **kwargs):
        if function in ['none', 'auto']:
            self.context['tool_choice'] = function
            self.context['tools'] = self.response.function.get_function_data(*args, **kwargs)
        elif type(function) == str:
            self.context.update({"type": "function", "function": {"name": function}})


class Response:
    """
    Generates prompts to be added to a OpenAI prompt object
    This holds only the message dictionary with the fields listed in self.fields
    """
    fields = {'content', 'role', 'function'}

    def __init__(self, *args, **kwargs ) -> None:
        # assistant message fields like self.fields
        self.content = None
        # self.role = gp_sts.assist_role
        self.legal_response = True
        self.function = Function(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self._get_assistant_message(*args, **kwargs)
        self._prep_response(*args, **kwargs)

    def _prep_response(self, *args, **kwargs):
        # NOTE: tool_calls is set by __dict__.update(response) in _get_assistant_message
        if self.function.get_func_call(self.tool_calls, *args, **kwargs):
            self.content = self._get_default_mst('f_call', *args, **kwargs)
        return self

    def _get_default_mst(self, default_type:str, *args, **kwargs):
        if default_type == 'f_call':
            f_args = []
            for k, v in self.function.arguments.items():
                if len(str(v)) >= 100:
                    f_args.append(f'{k}={str(v)[:100]}...,\n')
                else:
                    f_args.append(f'{k}={v},')
            return (
                        f"{sts.RED}Assistant requests function call:{sts.RESET}\n "
                        f"{self.function.name}"
                        f"{' '.join(f_args)} "
                        f"\navailable functions: \n"
                    ) + ''.join(['\n- ' + n for n in self.function.names])
        elif default_type == 'no_response':
            return 'Response._get_assistant_message: No text received!'



    def _get_assistant_message(self, response:object, *args, **kwargs):
        """
        Takes a response:ChatCompletionMessage and updates the Response instance with
                        'content': str
                        'role': str
                        'function_call': str or None
                        'tool_calls': list of str or None
        """
        if response.get('content') is None:
            response.update({'content': self._get_default_mst('no_response', *args, **kwargs)})
        elif re.search(r'<[^>]+>', response['content']):
            self.legal_response = False
        self.__dict__.update(response)


class Assistant:
    """
    Assistant handles the communication with an AI assistant of your choice.
    For the some assistants, Ollama is currently hosting and running the models. 
    See model_settings.models for the assistants and their respective models.
    The remote Ollama machines are listening on 0.0.0.0:11434 and are accessible 
    via the local private Network. 
    """
    
    def __init__(self, *args, d_assi:str=None, verbose: int = 0, **kwargs) -> None:
        self.d_assi = d_assi
        self.verbose = verbose
        self.running = False
        self.temperature: float = 0.0
        self.model, self.tag, self.host = self._determine_model(*args, **kwargs)

    def _determine_model(self, *args, model: str = None, **kwargs):
        """
        Determine the type of assistant based on the model.
        """
        md = self.d_assi if model is None else model
        for assistant, settings in gp_sts.models.items():
            if md in settings['models'].keys() or md in settings['models'].values():
                return *settings['models'][md], assistant
        print(f"{sts.YELLOW}Assistant._determine_model:{sts.RESET} {model = }, {md = }")
        msg = (  f"{sts.RED}Assistant._determine_model: Model not found! {sts.RESET}"
                f"Going with default model and assistant! "
                f"{sts.RED}(Possible costs apply!){sts.RESET}"
                )
        go = input(f"{msg}\nContinue? (y/n): ")
        if go.lower() != 'y':
            raise ValueError(msg)
        return gp_sts.default_model, None, gp_sts.d_assi

    def post(self, context: dict, *args, verbose: int = 0, **kwargs) -> dict:
        """
        Sends message to the appropriate assistant and handles the response.
        """
        if verbose:
            print(
                    f"Calling model:\n"
                    f"\thost: {sts.YELLOW}{self.host}{sts.RESET}: \n"
                    f"\tmodel: {sts.YELLOW}{self.model}{sts.RESET}"
            )
        # some assistants have multiple host instances i.ie (while_ai_0, while_ai_1)
        # they are nevertheless called via the same method name i.e. (while_ai)
        if re.search(r'_\d{1,2}$', self.host):
            method_name = '_'.join(self.host.split('_')[:-1])
        else:
            method_name = self.host
        return getattr(self, method_name)(context)

    def while_ai(self, context: dict, *args, model:str=None, **kwargs) -> dict:
        """
        Handles communication with a custom AI assistant.
        While-ai-0 hosts the large models and while-ai-1 the smaller models.
        """
        context['stream'] = False
        context['prompt'] = context['messages'][0]['content']
        if model == 'd3k': context['num_ctx'] = 256000
        r = requests.post(
                            gp_sts.models[self.host]['meta']['model_address'],
                            headers={'Content-Type': 'application/json'},
                            data=json.dumps(context)
        )
        r.raise_for_status()
        response = r.json()
        response.update({'tool_calls': None, 'content': response['response']})
        del response['response']
        return response

    def openAI(self, context: dict, *args, **kwargs) -> dict:
        """
        Handles communication with the OpenAI assistant.
        """
        self.client = OpenAI(api_key=gp_sts.get_api_key(self.host).get('key'))
        response = self.client.chat.completions.create(**context).choices[0].message.__dict__
        return response
