"""
test_data_py_module.py
Path: sts.test_data_dir/test_data_py_module.py
"""

import random

class NumberGuessingGame:
    def __init__(self):
        self.number_to_guess = random.randint(1, 100)
        self.guess = None

    def welcome_message(self):
        print("Welcome to the number guessing game!")

    def get_user_guess(self):
        self.guess = int(input("Guess a number between 1 and 100: "))

    def check_guess(self):
        """
        This is a method docstring
        """
        # this is a comment
        if self.guess < self.number_to_guess:
            print("Too low!")
            return False
        elif self.guess > self.number_to_guess:
            print("Too high!")
            return False
        else:
            print("Congratulations! You guessed the number.")
            return True

    @staticmethod
    def random_message():
        print("This is a random message.")

    def play_game(self):
        self.welcome_message()
        while not self.check_guess():
            self.get_user_guess()
