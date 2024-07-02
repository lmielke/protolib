# test_text.py
"""
Tests the Text class
"""

import unittest
import os
import re
import random as rd
import protopy.settings as sts
import protopy.helpers.collections as hlp
from protopy.gp.data.texts import Text


class Test_Text(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # text is loaded from sts.test_data_dir/test_text.txt
        cls.text = cls.mk_test_data()
        cls.verbose = 0

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def mk_test_data(cls):
        with open(os.path.join(sts.test_data_dir, 'test_text.txt'), 'r', encoding='utf-8') as f:
            text = f.read()
        return text

    ### Helper Function to Strip ANSI Codes ###

    # def strip_ansi_codes(self, text: str) -> str:
    #     """
    #     Strip ANSI escape sequences from a text string.
    #     Args:
    #         text (str): Text containing ANSI escape codes.
    #     Returns:
    #         str: Text with ANSI codes removed.
    #     """
    #     ansi_escape = re.compile(r'\x1b\[([0-9]+)(;[0-9]+)*m')
    #     return ansi_escape.sub('', text)

    # ### test_funcs start here ###

    def test_handle_existing_linebreaks(self):
        text_obj = Text(self.text)
        lines = text_obj.handle_existing_linebreaks()
        self.assertIsInstance(lines, list)
        self.assertGreater(len(lines), 0)

    def test_restore_existing_linebreaks(self):
        text_with_breaks = "This is a line.<lb>1. This is a list item."
        text_obj = Text(text_with_breaks)
        text_obj.restore_existing_linebreaks()
        self.assertIn("\n1. This is a list item.", text_obj.pretty)

    def test_strip_ansi_codes(self):
        ansi_text = "\x1b[31mThis is red text\x1b[0m"
        text_obj = Text(ansi_text)
        text_obj.strip_ansi_codes()
        self.assertNotIn("\x1b", text_obj.colored)
        self.assertEqual(text_obj.clean, "This is red text")

    def test_decolorize_text(self):
        """
        Test that decolorize_text removes all ANSI color codes from the text.
        """
        # Input string with ANSI color codes
        input_texts = [
                ("\x1b[31mRed Text\x1b[0m and \x1b[34mBlue Text\x1b[0m", "Red Text and Blue Text"),
                 (' \x1b[31madmin:\x1b[0m1 ', ' admin:1 '),
                 ('\x1b[37m►\x1b[39m \x1b[34mms_elly:\x1b[0m2 Hi, I am Ms_elly!', '► ms_elly:2 Hi, I am Ms_elly!'),
                 ('\x1b[37m►\x1b[39m \x1b[32mlars:\x1b[0m\3 Hi, I am Lars!', '► lars: Hi, I am Lars!'),
                    ]
        text_instance = Text(raw=input_texts[0][0])
        for text, expected in input_texts:
            decolorized = Text.decolorize_text(text)
            # Expected output should not contain any ANSI codes
            self.assertEqual(decolorized, expected, "ANSI color codes should be removed from the text.")


    def test_prettyfy_instructions(self):
        instructions = "These are some instructions that should be prettified."
        text_obj = Text(instructions, tag='instructs')
        text_obj.prettyfy_instructions(tag="instructs", verbose=2)
        start_tag, end_tag, color = sts.tags["instructs"]
        self.assertIn(start_tag, text_obj.pretty)  # Check for the actual tag

    def test_add_tags(self):
        content = "This is some content."
        text_obj = Text(content, tag='general')
        tagged_content = text_obj.add_tags(content)
        start_tag, end_tag, color = sts.tags['general']
        self.assertIn(start_tag, tagged_content)  # Check for the actual tag
        self.assertIn(end_tag, tagged_content)  # Check for the actual tag

    def test_hide_tags(self):
        tagged_text = "<INST>This is tagged content.</INST>"
        text_obj = Text(tagged_text, tag='instructs')
        text_obj.hide_tags(verbose=1)
        start_tag, end_tag, color = sts.tags["instructs"]
        self.assertIn(f"{color}{start_tag}...{end_tag}{sts.RESET}", text_obj.pretty)  # Check for the hidden tag

    def test_colorize_text(self):
        """
        Test that colorize_text converts ANSI color codes to HTML-like tags.
        """
        test_data, num_cnt, expecteds = "", 0, []
        for i in range(2):
            for name, color in sts.colors.items():
                num_cnt += 1
                # generate a string of random length between 10 and 50 characters
                random_text = os.urandom(rd.randint(0, 50)).hex()[:50]
                test_data += f"{num_cnt}: {color}This is a {name} text. {sts.RESET}!\n"
                expecteds.append((f"<{name}>", f"</{name}>"))
        text_obj = Text(raw=test_data)
        # print(text_obj.clean)
        text_obj.colorize_text()
        # print(text_obj.colored)
        for line, (start, end) in zip(text_obj.colored.split('\n'), expecteds):
            self.assertIn(start, line)
            self.assertIn(end, line)

    def test_strip_names(self):
        expert_name = "jhon_d"
        sts.experts = {expert_name: 'expert'}
        removables = (

                f"{expert_name}: This is a text with a name John Doe.",
                f" {expert_name}: This is a text with a name John Doe.",
                f" ► {expert_name}: This is a text with a name John Doe.",
                f" ► {expert_name}:  ► {expert_name}: This is a text with a name John Doe.",
                 "This is a text with a name John Doe.",
                 )
        non_removables = (
                            f"@{expert_name}: This is a text addressed to Jhon Doe.",
                            f" @{expert_name}: This is a text addressed to Jhon Doe.",
                            f"jhon_d: @{expert_name}: This is a text addressed to Jhon Doe.",
                            )
        for removable in removables:
            stripped = Text.strip_names(removable, expert_name)
            self.assertNotIn(expert_name, stripped)
            self.assertIn("This is a text with a name John Doe.", stripped)
        for non_removable in non_removables:
            stripped = Text.strip_names(non_removable, expert_name)
            self.assertEqual(f"@{expert_name}: This is a text addressed to Jhon Doe.", stripped)
if __name__ == "__main__":
    unittest.main()
