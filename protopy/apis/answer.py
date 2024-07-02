import getpass, os, sys, time
import random as rd
from protopy.gp.experts.experts import Expert
import protopy.helpers.collections as hlp
import protopy.settings as sts
import inspect

class ActionItem:
    """
    This ActionItem is for the completion of a spcific given action. The deliverable might be 
    answering a simple question.

    IMPORTANT NOTICE:
    The 'chat engine' might provide additional <instructions> and <infos> indicated by <tags> 
    These <tags> are exclusively used by the 'chat engine' to provide context to the question.
    It is ILLEGAL for any chat member to use <tags> inside the chat.

    Above chat members find context which could be relevant for answering the chat question.
    
    """

    def __init__(self, *args, **kwargs):
        self.try_count, self.max_tries = 0, 3
        self.temperature, self.d_temperature, self.max_temp = 0, 1.2 / self.max_tries, 1.0
        self.add_expert(*args, **kwargs)

    def add_expert(self, *args, expert:str=None, **kwargs):
        self.user = Expert(*args, name=getpass.getuser(), **kwargs)
        expert = expert if expert is not None else 'hanselman_s'
        self.expert = Expert(*args, name=expert, **kwargs)
        # print(self.expert.chat.to_table(tablefmt='plain', headers='', verbose=3))

    def run(self, *args, question:str, tool_choice:str=None, **kwargs):
        self.user.speak(inspect.getdoc(ActionItem), role='none')
        greeting = (
                    (f"Hi {self.expert.name}, I am {self.user.name}! How are you? "
                    f"Odd we are not allowed to use tags, ha. "),
                    (f"Yea strange, I guess that confuses the chat engine. Lets stick to the rules! "
                    f"Anyway, lets start. How can I help you today, {self.user.name}? "),
                    )
        self.user.speak(greeting[0], *args, role='none', **kwargs)
        self.expert.speak(greeting[1], *args, tool_choice='none', **kwargs)
        self.user.speak(question, *args, role='none', **kwargs)
        self.expert.speak(*args, tool_choice='none', instructs=None, **kwargs)
        print(self.expert.chat)
        return self.expert.last_said


def main(*args, **kwargs):
    answer = ActionItem(*args, **kwargs)
    return answer.run(*args, **kwargs)

if __name__ == "__main__":
    main()
