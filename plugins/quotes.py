import os
import pickle
import random

from plugin import Plugin


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return Quotes(data_dir, bot)


"""
Created by Matthew Klawitter 4/25/2019
Last Updated: 4/25/2019
"""


# Main class of the plugin that handles all commands and interactions
class Quotes(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot
        # Contains a list of quotes
        self.quotes = []
        self.load()

    def com_add(self, command):
        quote = command.args
        self.quotes.append(quote)
        self.save()
        return "Quotes: Added quote {} : {}".format(len(self.quotes) - 1, quote)

    def com_remove(self, command):
        quote_number = int(command.args)

        if (0 <= quote_number < len(self.quotes)):
            del self.quotes[quote_number]
            self.save()
            return "Quotes: Successfully removed quote number {}".format(quote_number)
        return "Quotes: Unable to remove quote number {}, it may be out of bounds or not an int.".format(quote_number)

    def com_list(self, command):
        return "Quotes: There are {} quotes available!".format(len(self.quotes))

    def com_view(self, command):
        quote_number = int(command.args)

        if (0 <= quote_number < len(self.quotes)):
            return "Quote #{}: {}".format(quote_number, self.quotes[quote_number])
        return "Quotes: The quote at {} doesn't seem to exist, it may be out of bounds or not an int.".format(quote_number)

    def com_random(self, command):
        if (len(self.quotes) > 0):
            random_number = random.randint(0, len(self.quotes) - 1)
            return "Quote #{}: {}".format(random_number, self.quotes[random_number])
        return "Quotes: Not enough quotes exist to pick one randomly!"

    # Saves players data from self.player_db
    def save(self):
        with open(self.dir + "/quotes.file", "wb") as f:
            pickle.dump(self.quotes, f)
            f.seek(0)
            f.close()

    # Loads players data into self.player_db
    def load(self):
        try:
            if os.path.getsize(self.dir + "/quotes.file") > 0:
                with open(self.dir + "/quotes.file", "rb") as f:
                    self.quotes = pickle.load(f)
                    f.seek(0)
                    f.close()
            print("Quotes: Quote file successfully loaded!")
        except FileNotFoundError:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)

            # Ensures that the pokebank file is created.
            with open(self.dir + "/quotes.file", "w+") as f:
                f.write("")
                f.seek(0)
                f.close()
            print("Quotes: No quotes file exists, creating a new one.")
            self.quotes = []
        

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "qadd":
            return {"type": "message", "message": self.com_add(command)}
        elif command.command == "qrm":
            return {"type": "message", "message": self.com_remove(command)}
        elif command.command == "qlist":
            return {"type": "message", "message": self.com_list(command)}
        elif command.command == "qview":
            return {"type": "message", "message": self.com_view(command)}
        elif command.command == "qrandom":
            return {"type": "message", "message": self.com_random(command)}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"qadd", "qrm", "qlist", "qview", "qrandom"}

    # Returns the name of the plugin
    def get_name(self):
        return "Quotes"

    # Run whenever someone types /help GroupNews
    def get_help(self):
        return "Commands:\n" \
                "'/qadd [quote]'\n"\
                "'/qrm [quote]'\n" \
                "'/qlist'\n" \
                "'/qview'[number]'\n" \
                "'/qrandom'\n" 
    
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