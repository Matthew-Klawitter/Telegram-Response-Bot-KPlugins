import os

from plugin import Plugin


def load(data_dir):
    return SetList(data_dir)


"""
Created by Matthew Klawitter 10/5/2017
"""


class SetList(Plugin):
    def __init__(self, data_dir):
        self.dir = data_dir
        self.setlist = {}

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        if not self.file_exists(self.dir + '/' + 'setlist' + '.txt'):
            with open(self.dir + '/' + 'setlist' + '.txt', 'w') as f:
                f.write("")
                f.close()

    def add_item(self, command):
        if not self.item_exists(command.args):
            with open(self.dir + '/' + 'setlist' + '.txt', 'a+') as f:
                f.write(command.args + "\n")
                f.close()
                return "Added " + command.args + " to the list!"
        return "Item already exists in the set!"

    def remove_item(self, command):
        if self.item_exists(command.args):
            file = open(self.dir + '/' + 'setlist' + '.txt', 'r').readlines()
            new_list = ""

            for item in file:
                if not item.__eq__(command.args + "\n"):
                    new_list += item

            with open(self.dir + '/' + 'setlist' + '.txt', 'w') as f:
                f.seek(0)
                f.write(new_list)
                f.close()

            return "Removed " + command.args + " from the set!"
        else:
            return "Unable to remove " + command.args + " from the set. It might not exist!"

    def list_items(self):
        with open(self.dir + '/' + 'setlist' + '.txt', 'r') as f:
            if self.file_exists(self.dir + '/' + 'setlist' + '.txt'):
                return "Here is a set of submitted items!" + "\n" + f.read()
            else:
                return "No items have been added to the set!"

    def item_exists(self, message):
        with open(self.dir + '/' + 'setlist' + '.txt.', 'r') as f:
            for item in f:
                if item.__eq__(message + "\n"):
                    return True
                else:
                    return False

    def file_exists(self, directory):
        return os.path.isfile(directory) and os.path.getsize(directory) > 0

    def on_command(self, command):
        if command.command == "additem":
            return self.add_item(command)
        elif command.command == "removeitem":
            return self.remove_item(command)
        elif command.command == "listitems":
            return self.list_items()

    def get_commands(self):
        return {"additem", "removeitem", "listitems"}

    def get_name(self):
        return "SetList"

    def get_help(self):
        return "/suggestitem @name, /removeitem @name, /listitems"
