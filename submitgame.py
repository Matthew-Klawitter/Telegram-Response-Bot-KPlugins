import os

from plugin import Plugin


def load(data_dir):
    return SubmitGame(data_dir)


"""
Created by Matthew Klawitter 9/27/2017
"""


class SubmitGame(Plugin):
    def __init__(self, data_dir):
        self.dir = data_dir
        self.submitgame = {}

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        if not self.file_exists(self.dir + '/' + 'gamelist' + '.txt'):
            with open(self.dir + '/' + 'gamelist' + '.txt', 'w') as f:
                f.write("")
                f.close()

    def add_game(self, command):
        if not self.game_exists(command.args):
            with open(self.dir + '/' + 'gamelist' + '.txt', 'a+') as f:
                f.write(command.args + "\n")
                f.close()
                return "Added " + command.args + " to the list!"
        return "Game already exists in list!"

    def list_game(self):
        with open(self.dir + '/' + 'gamelist' + '.txt', 'r') as f:
            return "Here is a list of submitted games!" + "\n" + f.read()

    def game_exists(self, command):
        with open(self.dir + '/' + 'gamelist' + '.txt.', 'r') as f:
            for game in f:
                if game.__eq__(command + "\n"):
                    return True
                else:
                    return False

    def file_exists(self, directory):
        return os.path.isfile(directory) and os.path.getsize(directory) > 0

    def on_command(self, command):
        if command.command == "suggestgame":
            return self.add_game(command)
        elif command.command == "listgames":
            return self.list_game()

    def get_commands(self):
        return {"suggestgame", "listgames"}

    def get_name(self):
        return "Submit Game"

    def get_help(self):
        return "/suggestgame @name, /listgames"
