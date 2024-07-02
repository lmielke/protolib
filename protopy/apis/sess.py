import getpass, os, sys, time
import random as rd
from protopy.gp.experts.experts import Expert
import protopy.helpers.collections as hlp
import protopy.settings as sts
import inspect

class Session:
    """
    This session is for the completion of a spcific given action. The session might be 
    about answering a question, without changing any state of any object. The session
    might also relate to a state modifying action that is latter performed by an expert.
    
    The session is all about providing a deliverable to the customer.
    Types of session deliverables are:
        - descriptions or explanations as plain text, (i.e. feature description)
        - lists and collections of elements, (i.e. sub-feature breakdown lists)
        - list of questions (i.e. clarifying questions regarding a feature)
        - code (snippets, methods, functions, classes, modules) as feature implementation
        - performed action (i.e. file creation/deletion, git commit/push, etc.)

    A session usually consists of 3 Phases indicated by individual question prefixes:
        1. Discussion Phase: The user asks the question and the experts provide 
            different answers. (i.e. The best way to solve this problem is ...)
        2. Decision Phase: The experts suggest a best option. 
            (i.e. We should go for ...´s suggestion, that ...)
            Decision: Finally the user or sudo decide which option to choose. 
            The decision should involve a concrete executable action. 
            (Example: Here is what we do! Use ls to list all files in your directory.)
            It should never be a follow up question.
        3. Execution Phase (if applicable): The choosen action is executed using a function.

    The session purpose is given in form of a question/problem that is asked by the user.
    A question is indicated by the key words 'Question/Problem:'
    The session is completed when the user has received a satisfactory answer to his question
    or the requested state change has been completed sucessfully.
    Example:
            user: "Question/Problem: How can I check my powershell version?"
            chris: 
                To check your PowerShell version, you can open PowerShell 
                and run the following command:
                ´´´powershell
                $PSVersionTable.PSVersion                                                              
                                                                                                     
                ´´´                                                                                     
                This command will display detailed information about the PowerShell 
                version you are using.
            sudo: We go with chris´s suggestion to check the powershell version using ...

    IMPORTANT NOTICE:
    The 'chat engine' will provide additional <instructions> and <infos> indicated by <tags> 
    These <tags> are exclusively used by the 'chat engine' to provide context to the question.
    It is ILLEGAL for any chat member to use <tags> inside the chat.
    
    """
    

    def __init__(self, *args, yes:bool=True, **kwargs):
        self.try_count, self.max_tries = 0, 3
        self.temperature, self.d_temperature, self.max_temp = 0, 1.2 / self.max_tries, 1.0
        self.success = False
        self.run_solver = yes
        self.add_experts(*args, **kwargs)
        self.phases_setup(*args, **kwargs)

    def add_experts(self, *args, experts: list = ['poppendieck_m'], **kwargs):
        self.experts = experts if experts is not None else ['poppendieck_m']
        self.expert = Expert(*args, name=self.experts[0], **kwargs)
        self.sudo = Expert(*args, name=sts.sudo, **kwargs)
        self.user = Expert(*args,   name=getpass.getuser(), role='user',
                                    instructs=f'Welcome {getpass.getuser()}!', **kwargs)

    def phases_setup(self, *args, **kwargs):
        self.question_indicator = f'Question/Problem: '
        self.discussion_indicator = f'Discussion Phase: '
        self.decision_indicator = f'Decision Phase: '
        self.phase_questions = [
                (
                    (   
                    f'{self.question_indicator}'
                    f'Make a suggestion how to solve {self.user.name}´s problem?'
                    ),
                    (
                    f'Read the {self.question_indicator}! '
                    f'Then answer the question.'
                    ),
                    (
                    f"Thanks for the welocme everyone, but can we focus on my question now?"
                    )
                ),
                (
                    (
                    f"{self.discussion_indicator}"
                    f'There must be a better way to solve {self.user.name}´s problem?'
                    ),
                    (
                    f'Carefully read the {self.question_indicator}! '
                    f'Analyse the problem, think step by step! '
                    f'Then thoughtfully answer the question. Be very specific.'
                    ),
                    (
                    f"Ok nice, I would like to hear all opinions?"
                    )
                ),
            ]
        self.num_phases = len(self.phase_questions)

    def discuss_and_decide(self, *args, question:str=None, **kwargs):
        def ask():
            # first the user asks the question
            self.user.speak((f"OK hope everyone has read and understood the infos above."
                            f" I have a question."), 
                            *args, role='user', **kwargs)
            self.sudo.speak(*args, **kwargs)
            q = f"{self.question_indicator}{question}" if question is not None else None
            self.user.speak(q, *args, role='user', **kwargs)
            self.user.speak((f" @{self.sudo.name}, can you rephrase the question for the team?"),
                            *args, role='user', **kwargs)
            # add comment why
            self.question = question if question is not None else self.user.last_said.content.text
            # self.user.speak(question, *args, role='user', **kwargs)
            self.sudo.speak(*args, 
                                instructs=(
                                    f'Lets get everyone on board by rephrasing '
                                    f'{self.user.name}´s {self.question_indicator}!'
                                    ), 
                                **kwargs
                            )
        def discuss():
            # then the experts provide different answers
            for i, (p_quest, p_instructs, p_user) in enumerate(self.phase_questions, 1):
                temperature = self.max_temp / i if i < (self.num_phases - 1) else 0
                for expert in sts.experts.values():
                    if expert.name == sts.sudo: continue
                    # re-emphasize on the question and ask to continue the discussion.
                    if expert.name == self.user.name:
                        p_quest = p_user
                    else:
                        self.sudo.speak(f"@{expert.name}: {p_quest}", instructs=p_instructs )
                        p_quest = None
                    # p_quest only filled when self.user is the expert in this loop
                    expert.speak(
                                    p_quest, *args, 
                                    role='assistant', function='none', temperature=temperature
                                    )
        def decide():
            kwargs.update({'tool_choice':'auto'})
            decision_q = (
                            f'Decision: Above you see the full chat, '
                            f'where I asked the following question: \n'
                            f'- {self.question} \n'
                            f'The chat then discussed the aspects and outlined viable options. '
                            f'- Now, based on the chat above, '
                            f'answer my question or provide the best solution for my problem ! '
                            f'Lets think it through step by step! '
                            )
            return self.user.ask(sts.sudo, decision_q, *args, role='user', **kwargs)
        ask()
        discuss()
        return decide()

    def single_shot_answer(self, *args, **kwargs):
        # discussion phase 
        # The agent first must understand what a session is
        # here we read the explanation of the session from the docstirng of this class
        self.sudo.speak(inspect.getdoc(Session))
        self.discuss_and_decide(*args, **kwargs)
        self.execute(*args, **kwargs)
        print(self.expert.chat.to_table(verbose=1, clear=False))
        print(self.sudo.chat.to_table(verbose=1, clear=False))
        print(self.user.chat.to_table(verbose=1, clear=False))

    def execute(self, *args, **kwargs):
        """
        We will now execute decision that has been made by the experts discussion.
        Execution is the final phase of the session and will produce the deliverable as
        outlined in sudos original session explanation.

        NOTE: 
        - Deeply analyse the prior discussion. Think very carefully! Think step by step!
        - If possible, use a function to run available commands on the user machine.
        - Otherwise, based on the discussion above, write down the desired deliverable.

        """
        # we add this methods docstring to the chat
        self.user.speak(inspect.getdoc(self.execute))
        self.expert.speak(role='assistant', function='auto', temperature=0.0)
        self.expert.execute()
        return self.user.last_heared.content.text

    def run(self, *args, **kwargs):
        if self.run_solver:
            self.solver(*args, **kwargs)
        else:
            return self.single_shot_answer(*args, **kwargs)

    def solver(self, *args, **kwargs):
        while not self.success:
            # print(f"\n{sts.YELLOW}### while loop: {self.try_count = } ###{sts.RESET}")
            print(self.expert.chat.to_table(verbose=2, clear=False))
            # print(self.expert.chat.messages[-2:])
            self.user_interaction(self.expert.exe_out, *args, **kwargs)
            if (not self.user.is_active) or (self.try_count > self.max_tries):
                return self.close('Ending session', *args, **kwargs)
            self.expert.speak(role='assistant', function='auto', temperature=self.temperature)
            self.expert.execute()
            if self.expert.exe_out.get('status') == False:
                self.sudo.ask(  to=sts.sudo,
                                question=(
                                            f'Explain very shortly what went wrong! \n'
                                            f'What {self.expert.name} should try instead!'
                                            ), 
                                name=self.sudo.name, 
                                role='assistant',
                                temperature=self.temperature
                )
                self.try_count += 1
                self.temperature += self.d_temperature

    def close(self, msg, *args, **kwargs):
        print(self.expert.chat.to_table(verbose=2, clear=False))
        print(f"{sts.RED}Quitting because {msg}!{sts.RESET}")
        self.sudo.chat.save_chat()
        return self.expert.last_heared

    def user_interaction(self, msg, *args, **kwargs):
        self.user.ask(self.expert.name, *args, role='user', function='none', **kwargs)
        # print(f"\tSession.user_interaction: {self.user.last_said.content.text = }\n\n")
        if self.user.last_said.content.text.endswith('quit'):
            self.user.is_active = 0
        else:
            self.user.is_active = 1

def main(*args, experts: list = ['poppendieck_m'], **kwargs):
    session = Session(experts=experts, *args, **kwargs)
    return session.run(*args, **kwargs)

if __name__ == "__main__":
    main()
