from dataclasses import dataclass, field
from typing import Optional, Dict, Tuple, ClassVar
import re
from textwrap import wrap as tw
import protopy.helpers.collections as hlp
import protopy.settings as sts
from protopy.gp.data.texts import Text  # Ensure you import the Text class correctly



@dataclass
class Content:
    text: Optional[str] = None
    instructs: Optional[str] = ''
    fmt: Optional[Text] = field(init=False, default=None)
    ifmt: Optional[Text] = field(init=False, default=None)
    code_blocks: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    tag: Optional[str] = None
    # use_tags: bool = True
    # fm: str = 'pretty'

    def __post_init__(self, *args, **kwargs):
        self.code_blocks = {}
        if self.text is not None:
            self.text = self.get_code_blocks(Text.correct_ansi_codes(self.text), *args, **kwargs)
            self.fmt = Text(*args, raw=self.text, **kwargs)
        if self.instructs is not None:
            self.instructs = self.get_code_blocks(Text.correct_ansi_codes(self.instructs), *args, **kwargs)
            self.tag = 'general' if self.tag is None else self.tag
            self.ifmt = Text(*args, raw=self.instructs, is_instructs=True, **kwargs)
        else:
            self.ifmt = Text(*args, raw='', **kwargs)

    def __str__(self, *args, **kwargs) -> str:
        return '\n'.join([str(vs) for vs in self.to_dict(*args, **kwargs).values()])

    def to_dict(self, *args, fm:str='white', **kwargs) -> dict:
        return {
            'instructs': self.ifmt.add_tags(getattr(self.ifmt, fm), *args, **kwargs) if self.ifmt else None,
            'code_blocks': hlp.colorize_code_blocks(self.code_blocks, *args, **kwargs),
            'text': getattr(self.fmt, fm) if self.fmt else None,
        }

    def get_code_blocks(self, text, *args, **kwargs) -> None:
        """ Extracts code blocks from the text and replaces them with placeholders """
        for ix, (lg, cd) in enumerate(sts.code_regex.findall(text), len(self.code_blocks)):
            key, code_text = f"<code_block_{ix}>", lg + cd
            wrapped = [tw(t, sts.inner_width) for t in cd.split('\n')]
            for i, lines in enumerate(wrapped):
                if len(lines) == 1:
                    pass
                else:
                    # in comments each line must start with a #
                    # linebreaks in code muyt be prefixed with a \
                    for j, line in enumerate(lines):
                        if j != 0: wrapped[i][j - 1] = wrapped[i][j - 1] + ' \\'
                        prefix = re.search(r'(^[ #]*)', lines[0])
                        if prefix:
                            pr = prefix.group(1)
                            if not line.startswith(pr):
                                wrapped[i][j] = pr + line
            wrapped = '\n'.join(['\n'.join(t) for t in wrapped])
            orig = '\n'.join([lg, cd])
            text = text.replace(f"```{code_text}```", key)
            self.code_blocks[key] = [lg, wrapped]
        return text

    def get_input(self, name=None, max_attempts=3, allow_empty=False, *args, **kwargs):
        """Prompts user for input with optional retries and empty input handling."""
        attempt_count = 0
        while attempt_count < max_attempts:
            user_input = input(f"\n{name.capitalize() if name else 'Enter'}: ")
            if user_input or allow_empty:
                self.text = user_input
                self.__post_init__(*args, **kwargs)
                return user_input
            else:
                print(f"No input detected from {name = }, please try again.")
                attempt_count += 1
        print(f"Maximum attempts reached without valid input. Exiting.")
        return None

    def construct(self, *args, fm:str='pretty', **kwargs):
        blocks = []
        content_dict = self.to_dict(*args, fm=fm, **kwargs)
        for k, vs in content_dict.copy().items():
            if k in ['instructs', 'text']:
                for n, cb in content_dict.get('code_blocks', {}).items():
                    content_dict[k] = content_dict[k].replace(n, cb)
        del content_dict['code_blocks']
        return ' ' +'\n'.join(content_dict.values()) + '\n'