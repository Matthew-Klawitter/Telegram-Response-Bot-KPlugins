import os
import random

from plugin import Plugin


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return Suggestions(data_dir, bot)


"""
Created by Matthew Klawitter 3/27/2019
Last Updated: 3/27/2019
"""


# Main class of the plugin that handles all commands and interactions
class Suggestions(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot
        # dict containing suggestions of type string and the amount of times they have been suggested
        self.list = {}

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
        random_suggestion = random.choice(self.list.keys())
        return "Randomly selected {}".format(random_suggestion)

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "slsuggest":
            return {"type": "message", "message": self.com_suggest(command)}
        elif command.command == "slrm":
            return {"type": "message", "message": self.com_remove(command)}
        elif command.command == "sllist":
            return {"type": "message", "message": self.com_list(command)}
        elif command.command == "slpick":
            return {"type": "message", "message": self.com_pick(command)}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"slsuggest", "slrm", "sllist", "slpick"}

    # Returns the name of the plugin
    def get_name(self):
        return "Suggestions"

    # Run whenever someone types /help GroupNews
    def get_help(self):
        return "Commands: \n, \
                '/slsuggest [suggestion]' \n,\
                '/slrm [suggestion]' \n, \
                '/sllist' \n, \
                '/slpick' \n" 