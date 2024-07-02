"""
system.py
sts.project_dir/protopy/helpers/sys_exec/system.py
This module provides the System class for executing shell and PowerShell commands.
The module also provides functionality for writing and modifying Python modules.
"""
import os, re, subprocess, time
from datetime import datetime as dt
from typing import List, Tuple, Union

from dataclasses import dataclass, field
import protopy.settings as sts


time_stamp = re.sub(r"([: .])", r"-" , f"{dt.now()}")


class System:

    def __init__(self, *args, role:str='system', **kwargs ) -> None:
        # assistant message fields like self.fields
        self.commands = None

    def __call__(self, msg:dict, *args, **kwargs):
        pass          

    def execute(self, *args, **kwargs):
        """
        Executes a shell command silently. Captures stdin and stdout, for analysis.
        """
        for command in self.commands:
            cmd = command.get('code')
            command['status'] = 'pending'
            if command.get('user_confirmed_execution'):
                cmd = cmd + ' -y' if 'proto' in cmd else cmd
                command['status'] = self.adhog_assist_shell_action(cmd, command.get('code'),)
            else:
                command['status'] = 'user rejected code execution'
        return self.commands

    def adhog_assist_ps_action(self, cmd:str, *args, **kwargs):
        """
        Executes powershell commands. To be used when the user asks the assistant 
        for an immediate action. If that action can be performed using a powershell command, 
        this function will do it.
            Example trigger prompts: 
                List all my files for the current directory.
                Clone proto into my user dir. Call the new project myclocklib.
                Create a file/folder named ...
                Show me tho OS info for my Windows.
        Args:
            cmd (str): The command to be executed by subprocess ps. Use any ps command.
                Examples:
                    - 'dir'
                    - 'ls'
                    - 'mkdir dir_name'
                    - 'echo "# filename.py" > filename.py'
                    - ...
        """
        # use subprocess to run provided command and return stdout
        # sometimes the assistent will use the 'powershell' prefix sometimes not
        cmd = cmd if cmd.startswith('powershell') else f'powershell -Command {cmd}'
        sh_out = subprocess.run(        cmd,
                                        text=True, shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                    )
        if sh_out.stdout:
            return {'status': True, 'body': self._clean_output(sh_out.stdout)}
        elif sh_out.stderr:
            return {'status': False, 'body': self._clean_output(sh_out.stderr)}
        else:
            return {'status': True, 'body': (   
                                            f'{sts.YELLOW}Function execution: {sts.RESET}'
                                            f'system.adhog_assist_ps_action, return == None'
                                            )
                    }

    def adhog_assist_shell_action(self, cmd:str, *args, **kwargs):
        """
        Executes shell commands. To be used when the user asks the assistant for an immediate
        action. If that action can be performed using a shell command, this function will do it.
            Example triggers: 
                List all my files for the current directory.
                Clone proto into my user dir. Call the new project myclocklib.
                Create a project named my_project ...
                Show me tho OS info for my Windows.
        Args:
            cmd (str): The command to be executed.
                Examples:
                    - 'dir'
                    - 'ls'
                    - 'mkdir dir_name'
                    - 'echo "# filename.py" > filename.py'
                    - ...
        """
        # use subprocess to run provided command and return stdout
        # sh_out = subprocess.run(cmd = cmd if exec == 'shell' else f'powershell -Command {cmd}',
        sh_out = subprocess.run(    f'powershell -Command {cmd}',
                                        text=True, shell=True,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                    )
        if sh_out.stdout:
            return {'status': True, 'body': self._clean_output(sh_out.stdout)}
        elif sh_out.stderr:
            return {'status': False, 'body': self._clean_output(sh_out.stderr)}
        else:
            return {'status': True, 'body': 'No output from command.'}

    def _clean_output(self, output):
        """
        Decode the byte string output from subprocess to a UTF-8 formatted string.

        Args:
            output (bytes): The byte string output from subprocess.

        Returns:
            str: A UTF-8 formatted string.
        """
        if isinstance(output, bytes):
            # Decode bytes to string using UTF-8 encoding
            return output.decode('utf-8')
        else:
            # If it's already a string, return as is
            return output
