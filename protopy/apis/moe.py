#state.py
import os, sys, getpass

from protopy.gp.experts.experts import Expert
import protopy.settings as sts
import protopy.helpers.collections as hlp

def main(*args, infos, experts:list, single_shot:bool=False, **kwargs):
    user = Expert(*args, name=getpass.getuser(), instructs='You have sudo!', **kwargs)
    for expert in experts:
        print(f"{expert = }")
        Expert(*args, name=expert, **kwargs)
        sts.experts[expert].ask(question=( 
                                f'Based on your instructions above, in a short sentence, '
                                f'name two facts about the underlying software, shown to you'
                                f' by the ### .* info ###! '
                                ), name=sts.sudo)
    while True:
        print(user.chat.to_table(verbose=2, clear=True))
        print(f"{sts.experts[sts.sudo].prompt.response.__dict__ = }")
        user.speak(role='user', **kwargs)
        if user.last_said.content.text.lower() in ['exit', 'quit', 'q']:
            break
        else:
            for expert in experts:
                sts.experts[expert].speak(role='assistant')
        if single_shot:
            return 

if __name__ == "__main__":
    main()
