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