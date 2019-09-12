import os
import pickle
import random

from plugin import Plugin


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return Suggestions(data_dir, bot)


"""
Created by Matthew Klawitter 3/27/2019
Last Updated: 6/12/2019
"""


# Main class of the plugin that handles all commands and interactions
class Suggestions(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot
        # dict containing lists of suggestions
        self.lists = {}
        self.load()

    def com_suggest(self, command):
        suggestion = command.args

        if suggestion in self.list.keys():
            self.list[suggestion] += 1
        else:
            self.list[suggestion] = 1
        return "Suggestion successfully added!"

    def com_remove(self, command):
        suggestion = command.args

        if suggestion in self.list.keys():
            del self.list[suggestion]
            return "Suggestion successfully removed!"
        return "That suggestion already doesn't exist!"

    def com_list(self, command):
        response = "The following suggestions have been made!\n"

        for suggestion in self.list.keys():
            response += "{}|{}\n".format(self.list[suggestion], suggestion)
        return response

    def com_pick(self, command):
        random_suggestion = random.choice(list(self.list.keys()))
        return "Randomly selected {}".format(random_suggestion)

    def com_clear(self, command):
        self.list = {}
        return "Successfully cleared suggestions"

    # Saves all lists
    def save(self):
        with open(self.dir + "/lists.file", "wb") as f:
            pickle.dump(self.lists, f)
            f.seek(0)
            f.close()

    # Loads all lists
    def load(self):
        try:
            if os.path.getsize(self.dir + "/lists.file") > 0:
                with open(self.dir + "/lists.file", "rb") as f:
                    self.lists = pickle.load(f)
                    f.seek(0)
                    f.close()
            print("SuggestionList: List file successfully loaded!")
        except FileNotFoundError:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)

            # Ensures that the pokebank file is created.
            with open(self.dir + "/lists.file", "w+") as f:
                f.write("")
                f.seek(0)
                f.close()
            print("SuggestionList: No List file exists, creating a new one.")
            self.lists = {}

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "sls":
            return {"type": "message", "message": self.com_suggest(command)}
        elif command.command == "slrm":
            return {"type": "message", "message": self.com_remove(command)}
        elif command.command == "sl":
            return {"type": "message", "message": self.com_list(command)}
        elif command.command == "slp":
            return {"type": "message", "message": self.com_pick(command)}
        elif command.command == "slc":
            return {"type": "message", "message": self.com_clear(command)}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"sls", "slrm", "sl", "slp", "slc"}

    # Returns the name of the plugin
    def get_name(self):
        return "SuggestionsList"

    # Run whenever someone types /help GroupNews
    def get_help(self):
        return "Commands:\n" \
                "'/sls [suggestion]' To make a suggestion\n" \
                "'/slrm [suggestion]' To remove a suggestion\n" \
                "'/sl' To list all suggestions\n" \
                "'/slp' To randomly pick a submission\n" \
                "'/slc' To clear the list" 

    def on_message(self, message):
        # Implement this if has_message_access returns True
        # message is some string sent in Telegram
        # return a response to the message
        return ""

    def has_message_access(self):
        return False
	
    def enable(self):
        pass

    def disable(self):
        pass