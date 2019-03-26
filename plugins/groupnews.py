import threading

from datetime import datetime
from plugin import Plugin
from time import sleep


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return GroupNews(data_dir, bot)


"""
Created by Matthew Klawitter 3/26/2019
Last Updated: 3/26/2019
"""


# Main class of the plugin that handles all commands and interactions
class GroupNews(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "":
            return {"type": "message", "message": "return msg"}
        elif command.command == "":
            return {"type": "message", "message": "return msg"}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"", ""}

    # Returns the name of the plugin
    def get_name(self):
        return "GroupNews"

    # Run whenever someone types /help GroupNews
    def get_help(self):
        return "'/' \n,\
                '/' \n"


