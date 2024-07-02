    def play_game(self):
        self.welcome_message()
        while not self.check_guess():
            self.get_user_guess()