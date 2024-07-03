#state.py
import os, sys, getpass

from protopy.gp.experts.experts import Expert
import protopy.settings as sts
import protopy.helpers.collections as hlp

def main(*args, experts:list, single_shot:bool=False, question:str=None, **kwargs):
    kwargs.update({'use_names': False, 'use_tags': False, 'single_shot': True})
    user = Expert(*args, name=getpass.getuser(), instructs='You have sudo!', **kwargs)
    for name in experts:
        Expert(*args, name=name, **kwargs)
        sts.experts[name].answer(asker_name=user.name,
                                question=(
                                f'Based on your instructions above, in a short sentence, '
                                f'name two facts about the underlying OS, shown to you'
                                f' by the ### .* info ###! '
                                ) if question is None else question, *args, **kwargs)
    while True:
        print(user.chats['master'].to_table(verbose=2, clear=True))
        user.speak(role='user', **kwargs)
        if user.last_said.content.text.lower() in ['exit', 'quit', 'clear', 'bye']:
            break
        else:
            for name in experts:
                sts.experts[name].speak(role='assistant')
        if single_shot:
            return 

if __name__ == "__main__":
    main()
