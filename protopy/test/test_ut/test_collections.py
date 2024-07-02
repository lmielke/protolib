# test_protopy.py

import os, re, shutil, sys, time, yaml
import unittest

# test package imports
from protopy.helpers.collections import group_text, pretty_print_messages
import protopy.settings as sts
import protopy.helpers.collections as hlp
import protopy.test.testhelper as helpers
import logging


class Test_Unittest(unittest.TestCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        cls.verbose = 0
        cls.testData = cls.mk_test_data(*args, **kwargs)
        cls.assist_text = """
            Certainly! To create your package named `myclock` in your user directory, run the following command in your terminal:  ```shell pipenv run proto clone -pr 'myclock' -n 'myclock' -a 'myclk' -t 'C:\\Users\\lars' -p 3.11 --install ```  \nThis will clone `protolib` to `C:/Users/lars/myclock`, set up the environment, and install dependencies.
        """

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        pass

    @classmethod
    def mk_test_data(cls, *args, **kwargs):
        with open(os.path.join(sts.test_data_dir, "test_protopy.yml"), "r") as f:
            out = yaml.safe_load(f)
        return out

    def test_pretty_print_messages(self, *args, **kwargs):
        messages = (
                    {'role': 'user', 'content': 'This is the user message.'},
                    {'role': 'assistant', 'content': self.assist_text},
                    )
        # print(f"\n{sts.YELLOW}Pretty print messages:{sts.RESET}")
        # pretty_print_messages(messages, *args, verbose=1, **kwargs)

    # def test_handle_tags(self):
    #     text = (
    #             f"<instructions> \nThese are your instructions\n </instructions>"
    #             f"There is also some fill text. <hierarchy> Some hierarchy.</hierarchy>"
    #             f"<pg_info> This is your pg_info </pg_info>"
    #             f"This is the actual question."
    #     )
    #     out = handle_tags(text)
    #     print(f"\n{sts.YELLOW}Doing nothing{sts.RESET}: {out}")
    #     out = handle_tags(text, tags=['pg_info'])
    #     print(f"\n{sts.YELLOW}Only pg_info{sts.RESET}: {out}")
    #     out = handle_tags(text, tags=['instructions', 'pg_info'])
    #     print(f"\n{sts.YELLOW}Instructions and pg_info{sts.RESET}: {out}")
    #     out = handle_tags(text, tags=['instructions', 'pg_info'], verbose=2)
    #     print(f"\n{sts.YELLOW}Instructions and pg_info verbose{sts.RESET}: {out}")

    def test_group_text(self):
        # NOTE: keep the first line at its current length for testing.

        out = group_text(self.assist_text, 70)
        # print(f"\nGrouped self.assist_text: {out}")


    def test_strip_ansi_codes(self):
        text = """
        @system: # EXPERT:  __'system'__ Hi, these are the instructions
        for expert __'system'__.   ## Some specific infos
        about the project environment. Current Project state for:
        network,system {'network,system': "\x1b[33m\nfor more
        infos:\x1b[0m\nproto info -i {'network', 'project', 'docker',
        'python', 'system'} or -v 1-3\n\x1b[32m\n###### PROTOPY USER info
        #######\x1b[0m\n\n\x1b[37m---------------------------------- CLONE
        INFO ----------------------------------\x1b[39m
        \n\x1b[33mNOTE:\x1b[39m to clone protopy use proto clone like
        this:\n\nproto clone \x1b[33m-pr\x1b[39m 'badylib' \x1b[33m-n\x1b[39m
        'badypackage' \x1b[33m-a\x1b[39m 'bady' \x1b[33m-t\x1b[39m '/temp'"""
        # print(text)
        # print('cleaned:')
        # print(hlp.strip_ansi_codes(text))

if __name__ == "__main__":
    unittest.main()
