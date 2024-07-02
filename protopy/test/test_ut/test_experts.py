# test_protopy.py

import logging
import os, re, time
import unittest
import yaml

from protopy.gp.experts.experts import Expert
import protopy.settings as sts
sts.max_experts = 10

import protopy.helpers.collections as hlp
from protopy.gp.data.tool_choice import FunctionToJson
f_json = FunctionToJson()



class Test_Expert(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.verbose = 0
        print(f"{sts.YELLOW} {cls.verbose = } {sts.RESET} Set to 1 to print chats.")
        cls.testData = cls.mk_test_data()
        cls.content = """
                                Certainly! To create your package named `myclocklib` in your 
                                temp directory, run the following command in your terminal:  
                                ```shell pipenv run proto clone -pr 'myclock' -n 'myclock' 
                                -a 'clock' -t 'C:\\temp' -p 3.11 --install ```  
                                \nThis will clone `protolib` to `C:/Users/lars/myclock`,
                                 set up the environment, and install dependencies.
                            """
        cls.code_blocks = """
            You can list all files in the current directory using the `ls` command on Unix-
           like systems or the `dir` command on Windows. Since you're using Windows, you
           can use the following command in your shell:

           ```shell

           dir

           ```

           If you want to list the files in a format similar to Unix systems, you can use:

           ```shell

           dir /B

           ```
        """

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def mk_test_data(cls):
        with open(os.path.join(sts.test_data_dir, "test_protopy.yml"), "r") as f:
            return yaml.safe_load(f)

    # @f_json.open_ai_function(apis={"open_ai_api_",}, write=True,)

    def test___init__(self):
        expected = "Be respectful to others."
        # sudo = Expert(name=sts.sudo)
        poppendieck_m = Expert(name='poppendieck_m', use_tags=False, use_names=False, color='blue')
        # self.sudo = Expert(name=sts.sudo)
        matches = list([m[1].lower() for m in re.findall(
                                r'(## proto info -i )(\w{2,20})( ##)', 
                                str(poppendieck_m.chats['master']))])
        self.assertEqual({'project', 'os_activity', 'os'}, set(matches))
        # chat should have chat instructions and expert instructions
        if self.verbose:
            print(str(poppendieck_m.chats['master']))
        self.assertEqual(poppendieck_m.chats['master'].owner.name, 'poppendieck_m')

    def test_load_instructions(self):
        name = 'ut_expert'
        ut_expert = Expert(name=name)
        instructs = ut_expert.load_instructions(infos=['docker'])
        # chat should contain docker infos
        self.assertIn('###### proto info -i DOCKER ######', instructs)
        # if self.verbose:
        #     print(f"\n{ut_expert.chats['master'].to_table(verbose=2)}")

    def test_set_name_regex(self,):
        # experts are added to the task
        name, color = 'ut_expert', 'green'
        expert = sts.experts.get(list(sts.experts.keys())[0])
        col_names = [
                            f"{expert.color_code}{name}{sts.RESET}",
                            f"{expert.color_code}{name}:{sts.RESET}",
                            f"{expert.color_code}{name}{sts.ST_RESET}",
                            f"{expert.color_code}{name}:{sts.ST_RESET}",
                            ]
        expected = ['', '', '', '']
        regex = expert.set_name_regex(name, color)
        out_names = [re.sub(regex.replace('[', r'\['), '', n[:40]) for n in col_names]
        self.assertEqual(expected, out_names)

    def test_listen(self,):
        # experts are added to the task
        name, color = 'richards_m', 'magenta'
        richards_m = Expert(name=name, color=color)
        # listen can be added as _think text
        richards_m.listen(text='I am listening')
        richards_m.listen(text='I am listening', instructs='Listen harder!')
        if self.verbose:
            print(f"\n{richards_m.chats['master'].to_table(verbose=2)}")
        self.assertEqual(richards_m.chats['master'].messages[-1].content.text, 'I am listening')

    def test_get_experts_infos(self, ):
        # experts are added to the task
        name, color = 'lars_m', 'green'
        expert = Expert(name=name, color=color)
        expert_infos = expert.get_experts_infos()
        self.assertTrue(expert_infos.startswith('###Available experts:'))

    def test__think(self, *args, **kwargs):
        name, color = 'springmeyer_d', 'yellow'
        guido = Expert(name=name, color=color)
        # print(f"{guido.last_heared = }")
        guido._think('I am thinking!')
        guido._think('I am thinking!', instructs=f'You are {guido.name}, Think more!')
        if self.verbose:
            print(f"\n{guido.chats['master'].to_table(verbose=2)}")

    def test_speak(self, *args, **kwargs):
        name, color = 'speaker', 'white'
        speaker = Expert(name=name, color=color)
        # print(f"{speaker.last_heared = }")
        # speaker.remember()
        # speaker.speak('I am speaking')
        # speaker.speak('I am speaking', instructs='Speak louder!')
        if self.verbose:
            print(f"\n{speaker.chats['master'].to_table(verbose=2)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
