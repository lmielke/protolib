"""
user_hist.py

This class collects various data about the recent user activity. Its purpose is to provide necessary context to an AI agent in order to perform user support related tasks.
"""
import json, os, re, sys
import winreg


class Userhistory:

    def __init__(self, *args, **kwargs):
        self.user_name = os.getenv('USER')
        self.cwd = os.getcwd()
        self.ps_history_file_path = self.get_ps_history_file_path(*args, **kwargs)
        self.recent_apps = self.get_recently_opened_apps(*args, **kwargs)

    def get_recently_opened_apps(self, *args, **kwargs) -> list:
        """
        Get a list of recently opened applications from the Windows registry.

        Returns:
            list: A list of recently opened applications.
        """
        recent_apps = []
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Search\RecentApps'
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                count = 0
                print(f"{count = }")
                while True:
                    try:
                        app_name = winreg.EnumKey(key, count)
                        print(f"{app_name = }")
                        recent_apps.append(app_name)
                        count += 1
                    except OSError as e:
                        print(f"{e = }")
                        
        except FileNotFoundError:
            pass
        return recent_apps


    def get_ps_history_file_path(self, *args, **kwargs) -> str:
        """
        Get the path to the PowerShell history file.

        Returns:
            str: The full path to the PowerShell history file.
        """
        appdata_path = os.getenv('APPDATA')
        if appdata_path:
            history_file_path = os.path.join(appdata_path, 'Microsoft', 'Windows', 'PowerShell', 'PSReadline', 'ConsoleHost_history.txt')
            if os.path.exists(history_file_path):
                return str(history_file_path)
            else:
                raise FileNotFoundError("PowerShell history file not found.")
        else:
            raise EnvironmentError("APPDATA environment variable not found.")


    def get_ps_history(self, text_len:int=100, *args, **kwargs):
        with open(self.ps_history_file_path, 'r') as f:
            recently_used_cmds = f.read().split('\n')
        # now remove all duplicate entries without changing the order of the cmds
        self.recently_used_cmds = []
        for cmd in recently_used_cmds:
            if cmd and (cmd not in self.recently_used_cmds):
                self.recently_used_cmds.append(cmd)
        self.recently_used_cmds = self.recently_used_cmds[-text_len:][::-1]
        return self.recently_used_cmds