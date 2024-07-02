"""
texts.py
##################### protopy Text #####################
manages the texts of the messages


"""

import re
import textwrap
from dataclasses import dataclass
from typing import List, Optional

import protopy.settings as sts

@dataclass
class Text:
    raw: str = ''
    clean: str = ''
    white: str = ''
    colored: str = ''
    pretty: str = ''
    is_instructs: bool = False
    tag: str = ''
    use_tags: bool = True

    def __post_init__(self, *args, **kwargs):
        if self.raw:
            self.clean = Text.correct_ansi_codes(self.raw)
            self.white = self.group_text(Text.decolorize_text(self.clean))
            self.colored = self.colorize_text(self.clean)# to be discarded (not usable)
            self.pretty = self.group_text(self.clean)
        if not self.is_instructs or not self.raw:
            self.is_instructs = True if self.tag else False
            self.is_instructs = False if not self.raw else self.is_instructs

    def __str__(self, *args, **kwargs):
        return f"Text(raw={self.raw[:30]}..., {self.tag = }, {self.is_instructs = })".replace('\n', ' ')

    @staticmethod
    def correct_ansi_codes(clean: str, *args, **kwargs) -> str:
        """
        Corrects ANSI escape sequences in the given clean.

        Fixes any incorrect ANSI escape sequences to ensure proper display.

        Args:
            clean (str): The clean to correct.

        Returns:
            str: The corrected clean.
        """
        for incorrect, correct in sts.ansi_replaces.items():
            clean = clean.replace(incorrect, correct)
            clean = clean.replace('\\\\', '/')
        return clean

    def group_text(self, text:str=None, char_len: int=sts.table_width, *args, **kwargs) -> None:
        """
        Groups the clean by a specified character length.

        Args:
            char_len (int): The character length to group the clean by.
        """
        text = text if text is not None else self.clean
        texts = self.handle_existing_linebreaks(text, char_len, *args, **kwargs)
        texts = [textwrap.wrap(t, width=char_len) for t in texts]
        texts = ['\n'.join(t) for t in texts]
        # sometimes there is lengthy sequences of speces in the text. So I remove 
        # whats longer than a tab.
        texts = [t.replace('     ', ' ') for t in texts]
        self.pretty = '\n'.join(texts).strip()
        return self.pretty

    def handle_existing_linebreaks(self, text: str = None, *args, **kwargs) -> List[str]:
        """
        Handles existing line breaks in the text.

        Ensures proper formatting by managing existing line breaks.

        Args:
            text (str): The text to process. If None, self.raw is used.

        Returns:
            List[str]: List of text segments split by line breaks.
        """
        text = text if text is not None else self.clean
        texts = re.split(r'(\r\n|\r|\n)', text)
        texts = [t.strip() for t in texts if t.strip()]
        return texts


    def restore_existing_linebreaks(self, *args, **kwargs) -> None:
        """
        Restores existing line breaks in the clean.

        Preserves the raw line breaks and adjusts them as needed.
        """
        clean = re.sub(r'(<lb>\s*)(\d+\.\s)', r'\n\2', self.raw)
        clean = re.sub(r'(<lb>\s*)(-\s*)', r'\n\2', clean)
        clean = re.sub(r'(<lb>\s*)(<code_block_\d+>\s*)(<lb>\s*)', r'\n\2\n', clean)
        clean = re.sub(r'\n(\n\d+\.\s|\n-\s|\n<code_block_\d+\s)', r'\1', clean)
        clean = re.sub(r'\n<lb>\s*', r'\n', clean)
        clean = re.sub(r'\s*<lb>\s*', r' ', clean)
        self.pretty = clean

    def strip_ansi_codes(self, *args, **kwargs) -> None:
        """
        Strips ANSI escape sequences from the clean.

        Removes color and formatting codes to clean the clean.
        """
        ansi_escape = re.compile(r'\x1b\[([0-9]+)(;[0-9]+)*m')
        self.clean = ansi_escape.sub('', self.raw)

    def prettyfy_instructions(self, text:str=None, *args, verbose: int = 1, **kwargs) -> None:
        """
        Prettifies instructions in the clean based on verbosity.

        Formats instructions for better readability.

        Args:
            tag (str): The tag to apply.
            verbose (int): Verbosity level for formatting.
        """
        if not self.clean: return ''
        if verbose == 0:
            pretty = ''
        if verbose >= 2:
            self.group_text(text, sts.inner_width, *args, **kwargs)
            pretty = self.pretty.replace('\n', '\n\t')
        elif verbose >= 1:
            self.group_text(text, sts.inner_width, *args, **kwargs)
            pretty = self.pretty.replace('\n', '\n\t')[:sts.visible_chars]
            hidden_chars = max(len(self.raw) - sts.visible_chars, 0)
            if hidden_chars:
                pretty += (
                        f"\n\t...[hidden {hidden_chars} characters], "
                        f"verbose={verbose}"
                        )
        else:
            pretty = ''
        self.pretty = self.add_tags(pretty, *args, **kwargs)

    def add_tags(self, texts: str, *args, tag: str=None, use_tags:bool=True, **kwargs) -> str:
        """
        Adds specified tags to the clean texts.

        Tags are used to mark sections of the clean for various purposes.

        Args:
            texts (str): The texts to add tags to.
            tag (str): The tag to add to the clean.
        
        Returns:
            str: The texts with added tags.
        """
        tag = tag if tag else self.tag
        if use_tags and not tag:
            tag = 'instructs'
        if not self.is_instructs or not use_tags:
            return texts
        elif not self.use_tags:
            return f"Here are some infos about the {tag}:\n {texts}\n"
        else:
            start, end, color = sts.tags.get(   tag, 
                                                (f'<{tag}_info>', f'</{tag}_info>', sts.DIM)
                                )
            return (
                    f"{color}{start}{sts.RESET}{sts.ST_RESET}\n"
                    f"{texts}\n"
                    f"{color}{end}{sts.RESET}{sts.ST_RESET}"
                    )

    def hide_tags(self, verbose: int = 0, *args, **kwargs) -> None:
        """
        Removes all tag-enclosed contents from the clean.

        Adjusts the removal process based on verbosity.

        Args:
            verbose (int): Verbosity level for hiding tags.
        """
        clean = self.pretty or self.clean
        for tag, (start, end, color) in sts.tags.items():
            if verbose == 0:
                # Remove the tag-enclosed texts entirely
                replacement = r''
            elif verbose <= 1:
                # Replace the tag-enclosed texts with a summary
                replacement = f"{color}{start}...{end}{sts.RESET}"
            else:
                # Replace the tag-enclosed texts with the full tag and ellipsis
                replacement = f'\n{color}{start}...{end}{sts.RESET}\n'
            clean = re.sub(fr'{re.escape(start)}.*?{re.escape(end)}', replacement, clean, flags=re.DOTALL)
        self.pretty = clean


    def colorize_text(self, clean: str = None, *args, **kwargs) -> None:
        """
        Replaces ANSI color codes with HTML-like tags in the text.

        Args:
            clean (str): The text to be colorized. If None, self.clean is used.
        """
        if clean is None:
            clean = self.clean

        colorized_text = []
        active_tag = None
        ansi_pattern = re.compile(r'(\x1b\[\d+m)')
        parts = ansi_pattern.split(clean)
        reverse_colors = {v: k for k, v in sts.colors.items()}
        resets = {sts.RESET: sts.ST_RESET}
        current_color, next_color, ps, cnt = False, None, [], 0
        for i, part in enumerate(parts):
            if ansi_pattern.match(part):
                next_color, reset = reverse_colors.get(part, None), part in resets
                if current_color == False:
                    o_tag, c_tag = f"<{next_color}>", f"</{next_color}>"
                    current_color = next_color
                    continue
                elif current_color != next_color and next_color is not None:
                    colorized_text.append(o_tag + ' '.join(ps) + c_tag)
                    o_tag, c_tag = f"<{next_color}>", f"</{next_color}>"
                    current_color, ps = next_color, []
                elif reset:
                    ps.insert(cnt, o_tag)
                    ps.append(c_tag)
                    colorized_text.append(' '.join(ps))
                    current_color, cnt, ps = False, 0, []
            else:
                ps.append(part)
                if current_color == False:
                    cnt += 1
        return ''.join(colorized_text)

    @staticmethod
    def decolorize_text(text: str) -> str:
        """
        Remove ANSI color codes and other non-printable characters from the provided text.

        Args:
            text (str): The input text with ANSI color codes and other non-printable characters.

        Returns:
            str: The text with color codes and non-printable characters removed.
        """
        if text is None:
            return None

        # Pattern to match ANSI color codes
        ansi_color_pattern = re.compile(r'\x1b\[[0-9;]*m')
        text = ansi_color_pattern.sub('', text)

        # Pattern to match other non-printable ASCII characters
        non_printable_pattern = re.compile(r'[\x00-\x1F\x7F]')
        cleaned_text = non_printable_pattern.sub('', text)
        
        return cleaned_text


    @staticmethod
    def strip_names(text, name:str=None, *args, **kwargs):
        """
        Strips the name from the text if the name is found in the text.
        This method uses a regex stored in the `sts.experts` dictionary to find and remove
        names from the text, particularly names that might be prefixed with ANSI color codes.

        Args:
            name (str): The name to remove.
            text (str): The text from which to remove the name.

        Returns:
            str: The text with the name removed.
        """
        names = [name] if name is not None else list(sts.experts.keys())
        # all names are removed from the betinning of the text
        for name in names:
            # Remove the name from the text
            # if however the name is used to address an expert, like: @poppendieck_m, 
            # then the name is not removed
            addr_regex = r"(\W*)(@" + name + r":?)\s*"
            addr_match = re.search(addr_regex, text)
            # when a addr_match is found its temporaryly replaced with <addr_match>
            if addr_match:
                text = text.replace(addr_match[0], '<addr_match>')
            # now whats left of name is removed from the beginning of the text
            regex = re.compile(r'^\W*' + f'{name}' + r'\W*', re.IGNORECASE)
            while True:
                replaced = regex.sub('', text)
                if replaced == text:
                    break
                text = replaced
            # the <addr_match> is replaced back with the addr_match
            if addr_match:
                text = text.replace('<addr_match>', f"{addr_match[2].strip()} ")
                text = text.replace('addr_match>', f"{addr_match[2].strip()} ")
        return text

    @staticmethod
    def whiten(text, *args, **kwargs):
        """
        Whiten the text by removing all ANSI color codes from the text.
        """
        return Text.strip_names(Text.decolorize_text(text))
