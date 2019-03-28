import os
import pickle
import random

from libs.honorbank import HonorBank
from plugin import Plugin


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return CafeGacha(data_dir, bot)


"""
Created by Matthew Klawitter 3/27/2019
Last Updated: 3/27/2019
"""


# Main class of the plugin that handles all commands and interactions
class CafeGacha(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot
        #
        self.accounts = HonorBank()
        #
        self.gacha_manager = GachaManager(self.dir)

    def com_summon(self, command):
        user = command.user.username
        honor_spent = int(command.args)

        if not self.accounts.account_exists(user):
            self.accounts.create_account(user)

        if honor_spent < 1000:
            return {"type": "message", "message": "CafeGacha: You need to spend at least 1000 to summon a new minion!"}

        if self.accounts.get_funds(user) >= honor_spent:
            modifier = int(honor_spent / 1000)
            self.accounts.charge(user, honor_spent)

            if modifier > 3:
                modifier = 3
            elif modifier < 0:
                modifier = 0

            new_gacha = self.gacha_manager.pick_gacha(modifier)
            self.gacha_manager.give_gacha(new_gacha, user)
            return {"type": "photo", "caption": "CafeGacha: You summoned {}".format(new_gacha.name), "file_name": new_gacha.uri}
        return {"type": "message", "message": "CafeGacha: You do not possess {} honor!".format(honor_spent)}

    def com_view(self, command):
        gacha_name = command.args
        gacha = self.gacha_manager.get_gacha(gacha_name)
        return gacha.uri

    def com_list(self, command):
        user = command.user.username
        gacha_owned = self.gacha_manager.list_owned(user)
        response = "CafeGacha: You own the following:\n"
        
        for gacha in gacha_owned:
            response += "{} | {}".format(gacha[0], gacha[1])
        return response

    def com_trade(self, command):
        user_from = command.user.username
        args = command.args.split(" ")
        user_to = args[0]
        del args[0]
        gacha_name = "".join(args)

        if self.gacha_manager.trade(gacha_name, user_from, user_to):
            return "CafeGacha: Successfully traded your {} to {}".format(gacha_name, user_to)
        return "CafeGacha: Trade failed! Either you do not possess enough of that gacha, or that user isn't currently playing this game... "

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "gsummon":
            return self.com_summon(command)
        elif command.command == "gview":
            return {"type": "photo", "caption": "", "file_name": self.com_view(command)}
        elif command.command == "glist":
            return {"type": "message", "message": self.com_list(command)}
        elif command.command == "gtrade":
            return {"type": "message", "message": self.com_trade(command)}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"gsummon", "gview", "glist", "gtrade"}

    # Returns the name of the plugin
    def get_name(self):
        return "CafeGacha"

    # Run whenever someone types /help GroupNews
    def get_help(self):
        return "'/gsummon [summon-level]' \n,\
                '/gview' \n, \
                '/glist' \n, \
                '/gtrade' \n" 


class GachaManager():
    def __init__(self, dir):
        self.dir = dir
        self.player_db = {}
        self.load()
        self.bronze_list = self.build_gacha("Bronze")
        self.silver_list = self.build_gacha("Silver")
        self.gold_list = self.build_gacha("Gold")

    def build_gacha(self, rarity):
        try:
            new_list = []

            for file in os.listdir(self.dir + "/" + rarity):
                if file.endswith(".png"):
                    new_list.append(Gacha(file.split(".")[0], self.dir + "/" + rarity + "/" + file))
            return new_list
        except NotADirectoryError:
            print("CafeGacha: No data could be loaded!")
            return new_list

    def pick_gacha(self, modifier):
        draw_chance = random.randint(0,99) + (modifier * 10)

        if 0 <= draw_chance < 75: # 75% chance at bronze
            return random.choice(self.bronze_list)
        elif 75 <= draw_chance < 97: # 22% chance of silver
            return random.choice(self.silver_list)
        else: # 3% chance of gold
            return random.choice(self.gold_list)

    def give_gacha(self, gacha, username):
        if not username in self.player_db.keys():
            self.player_db[username] = {}

        if gacha.name in self.player_db[username].keys():
            self.player_db[username][gacha.name] += 1
            self.save()
        self.player_db[username][gacha.name] = 1
        self.save()

    def get_gacha(self, name):
        for item in self.bronze_list:
            if item.name == name:
                return item

        for item in self.silver_list:
            if item.name == name:
                return item

        for item in self.gold_list:
            if item.name == name:
                return item
        return None

    def list_owned(self, username):
        owned = []

        if username in self.player_db.keys():
            for item in self.player_db[username].keys():
                owned.append([item, self.player_db[username][item]])
            return owned
        return owned

    def trade(self, name, user_from, user_to):
        if user_from in self.player_db.keys():
            if user_to in self.player_db.keys():
                for item in self.player_db[user_from].keys():
                    if item == name:
                        if self.player_db[user_from][item] >= 1:
                            self.player_db[user_from][item] -= 1
                            self.player_db[user_to][item] += 1
                            self.save()
                            return True
        return False

    # Saves players data from self.player_db
    def save(self):
        with open(self.dir + "/players.file", "wb") as f:
            pickle.dump(self.player_db, f)
            f.seek(0)
            f.close()

    # Loads players data into self.player_db
    def load(self):
        try:
            if os.path.getsize(self.dir + "/players.file") > 0:
                with open(self.dir + "/players.file", "rb") as f:
                    self.player_db = pickle.load(f)
                    f.seek(0)
                    f.close()
            print("CafeGacha: Users file successfully loaded!")
        except FileNotFoundError:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)

            # Ensures that the pokebank file is created.
            with open(self.dir + "/players.file", "w+") as f:
                f.write("")
                f.seek(0)
                f.close()
            print("CafeGacha: No gacha file exists, creating a new one.")
            self.player_db = {}

class Gacha():
    def __init__(self, name, uri):
        self.name = name
        self.uri = uri