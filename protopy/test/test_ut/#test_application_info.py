"""
Tests the ApplicationInfo class

NOTE: Currently this test runs a background service that can not be stopped. This is
why the test is inactive. Enable the test when working with it.
"""

import unittest
import os
from pynput.keyboard import KeyCode
from protopy.helpers.application_logger.application_info import ApplicationInfo
import logging
from pynput.keyboard import Key, KeyCode

print("Test_ApplicationInfo")

class Test_ApplicationInfo(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.log_dir = os.path.expanduser("~/.testlogs/windows_test")
        cls.app_info = ApplicationInfo(pause_threshold=300)

    @classmethod
    def tearDownClass(cls):
        # Close logging handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
            handler.close()

        # Clean up log directory after tests
        if os.path.exists(cls.log_dir):
            for file in os.listdir(cls.log_dir):
                file_path = os.path.join(cls.log_dir, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            os.rmdir(cls.log_dir)

    ###  Tests start here ###


    def test_get_str_representation(self):
        """
        Test the get_str_representation method
        """
        test_cases = [
            (KeyCode(char='a'), 'a'),
            (KeyCode(char='\x03'), '\x03'),  # Ctrl+C
            (Key.enter, '[enter]'),
            ('\x01', '\x01'),  # Ctrl+A
            ('a', 'a')
        ]

        for key, expected in test_cases:
            with self.subTest(key=key, expected=expected):
                result = self.app_info.get_str_representation(key)
                self.assertEqual(result, expected)

    def test_load_log_file(self, *args, **kwargs):
        file_name, result = ApplicationInfo.load_log_file('today', *args, **kwargs)
        for k, vs in result.items():
            print(f"\n{k = }: {vs}")

    def test_ctrl_mapping(self):
        """
        Test the ctrl_mapping method with various control keys
        """
        test_cases = {
            '\x01': 'a',  # Ctrl+A
            '\x02': 'b',  # Ctrl+B
            '\x03': 'c',  # Ctrl+C
            '\x04': 'd',  # Ctrl+D
            '\x05': 'e',  # Ctrl+E
            '\x06': 'f',  # Ctrl+F
            '\x07': 'g',  # Ctrl+G
            '\x08': 'h',  # Ctrl+H
            '\x09': 'i',  # Ctrl+I
            '\x0A': 'j',  # Ctrl+J
            '\x0B': 'k',  # Ctrl+K
            '\x0C': 'l',  # Ctrl+L
            '\x0D': 'm',  # Ctrl+M
            '\x0E': 'n',  # Ctrl+N
            '\x0F': 'o',  # Ctrl+O
            '\x10': 'p',  # Ctrl+P
            '\x11': 'q',  # Ctrl+Q
            '\x12': 'r',  # Ctrl+R
            '\x13': 's',  # Ctrl+S
            '\x14': 't',  # Ctrl+T
            '\x15': 'u',  # Ctrl+U
            '\x16': 'v',  # Ctrl+V
            '\x17': 'w',  # Ctrl+W
            '\x18': 'x',  # Ctrl+X
            '\x19': 'y',  # Ctrl+Y
            '\x1A': 'z'   # Ctrl+Z
        }

        for hex_code, expected_char in test_cases.items():
            with self.subTest(hex_code=hex_code, expected_char=expected_char):
                key = KeyCode(char=hex_code)
                result = ApplicationInfo.ctrl_mapping(ApplicationInfo.get_str_representation(key))
                self.assertEqual(result, expected_char)

if __name__ == "__main__":
    unittest.main()
