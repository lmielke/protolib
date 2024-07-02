import getpass, os, sys, time
import random as rd
from protopy.gp.models.openai.prompt import Prompt
from protopy.gp.data.message import Message
from protopy.gp.data.chat import Chat
from protopy.gp.data.skill import Skill
# import protopy.helpers.collections as hlp
import protopy.settings as sts
from protopy.apis.info import main as info_main
import inspect


class Question:
    """
    A simple question that needs answering.
    Keep you answer short and concise. 

    Now:
    """


    def __init__(self, *args, model:str='l3b', verbose=1, **kwargs):
        self.start_time = time.time()
        self.try_count, self.max_tries = 0, 3
        self.temperature, self.d_temperature, self.max_temp = 0, 1.2 / self.max_tries, 1.0
        self.name = getpass.getuser()
        self.d_assi, self.role = model, 'user'
        self.verbose = verbose
        # setting up the chat starts here
        self.chat = Chat(
                            owner=self,
                            instructs='You are a helpful chatbot!', 
                            use_tags=False, 
                            use_names=False, 
                            chat_type='question'
                    )
        self.chat.initialize(*args, **kwargs)
        self.skills = self.add_skills(*args, **kwargs)

    def add_skills(self, *args, skills:list=[], **kwargs):
        if not skills:
            return []
        sks = []
        for skill in skills:
            skill = Skill(name=skill)
            sks.append(skill)
            self.chat.add_instructions(skill.instructs)
        return sks


    def run(self, *args, question:str, function:str=None, **kwargs):
        answer, user_response = None, False
        self.chat.append(question, role='user')
        self.chat.get_model_response(*args, 
                                            single_shot=True, 
                                            function=function,
                                            to_chat=True, **kwargs
                                            )
        # self.chat.append(Message(name='assistant', content=rs.get('content'), role='assistant'))
        exe = self.chat.prompt.response.function.execute()
        if exe:
            self.chat.append(exe, role='system')
            print(self.chat.to_table(verbose=1))
        if self.verbose:
            print(self.chat.to_table(verbose=1))
        self.chat.append(None, role='user')
        user_response = self.chat.messages[-1].content.text
        if any([word in user_response for word in ['thanks', 'bye', 'clear']]):
            if user_response.strip() == 'clear':
                os.system('cls')
            return str(self.chat.messages[-2]), None
        else:
            return None, user_response


def main(*args, question:str=None, **kwargs):
    q, answer = Question(*args, **kwargs), None
    while answer is None:
        answer, question = q.run(*args, question=question, **kwargs)
    print(f"Prompt duration: {sts.YELLOW}{time.time() - q.start_time}{sts.RESET}")
    return answer

if __name__ == "__main__":
    main()
