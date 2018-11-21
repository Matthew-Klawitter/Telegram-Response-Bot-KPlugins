import datetime
import json
import os
import pickle
import random
import socket
import threading
from struct import pack, unpack

from plugin import Plugin
from time import sleep


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return CatchEmAll(data_dir, bot)


"""
Created by Matthew Klawitter 11/19/2018
Last Updated: 11/21/2018
Version: v2.0.0.0
"""


# Main class of the plugin that handles all commands and interactions
class CatchEmAll(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data '/catchemall'
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot
        # A set containing all channels in which to send alerts to
        self.channels = set()
        # Flag indicating if there is a current pokemon encounter available
        self.encounter_exists = False
        # A Pokemon object containing and available pokemon encounter
        self.current_encounter = None
        # A PokeBank object containing data on users and the pokemon they own
        self.poke_bank = PokeBank(self.dir)
        # A PokemonManager object containing data on all pokemon and methods to find information and generate them
        self.poke_manager = PokemonManager(self.dir)

        # Launches a deamon thread that handles alerts and random encounters
        thread = threading.Thread(target = self.encounter)
        thread.daemon = True
        thread.start()

    # Adds a pokemon to a specific users personal pokemon bank (self.poke_bank)
    def com_catch(self, command):
        user = command.user.username

        if not self.encounter_exists:
            return "Catch em' All: There is no encounter, check back later!"

        if self.current_encounter == None:
            return "Catch em' All: Sorry " + user + ", you missed your chance!"

        self.poke_bank.store_mon(user, self.current_encounter)
        poke = self.current_encounter
        self.current_encounter = None
        self.encounter_exists = False
        return "Catch em' All: Congrats " + user + " you caught {} (cp:{})!".format(poke.name, str(poke.cp))

    # Lists all pokemon within a user's pokemon bank (dict) should they exist
    def com_list(self, command):
        user = command.user.username
        if self.poke_bank.user_exists(user):
            bank = self.poke_bank.user_list(user)
            index = 0
            message = "Here are the contents of {}'s bank\n".format(user)
        
            for pokemon in bank:
                message += str(index) + ": " + pokemon.name + "| cp: " + str(pokemon.cp) + "\n"
                index += 1
            return message
        return "Catch em' All: You do not possess an account!"

    # Releases a pokemon from a users bank given a specific location within the bank (users find locations with /poke_list)
    def com_release(self, command):
        commands = command.args.split(" ")

        if len(commands) == 1: 
            user = command.user.username

            if self.poke_bank.user_exists(user):
                poke = self.poke_bank.get_mon(user, int(commands[0]))
                if not poke == None:
                    self.poke_bank.remove_mon(user, int(commands[0]))
                    return "Catch em' All: You have released your {} (cp:{})... goodbye...".format(poke.name, str(poke.cp))
                return "Catch em' All: The location you specified does not exist!"
            return "Catch em' All: You do not possess an account!"
        return "Catch em' All: Invalid syntax - use /poke_list [bank_id]"

    # Shows stats of a specified pokemon within a users bank (users find locations with /poke_list)
    def com_stat(self, command):
        commands = command.args.split(" ")

        if len(commands) == 1: 
            user = command.user.username

            if self.poke_bank.user_exists(user):
                poke = self.poke_bank.get_mon(user, int(commands[0]))
                if not poke == None:
                    return poke.__str__()
                return "Catch em' All: The location you specified does not exist!"
            return "Catch em' All: You do not possess an account!"
        return "Catch em' All: Invalid syntax - use /poke_stat [bank_id]"

    # Admin command to grant pokemon to specific users
    def com_grant(self, command):
        user = command.user.username
        commands = command.args.split(" ")

        if len(commands) == 2: 
            if user == "Klawk":
                if self.poke_manager.find_pokemon(commands[1]):
                    self.poke_bank.store_mon(commands[0], self.poke_manager.generate_exact_pokemon(commands[1]))
                    return "Catch em' All: Granted {} the pokemon {}!".format(commands[0], commands[1])
                return "Catch em' All: Sorry, that pokemon does not exist!"
            return "Catch em' All: Sorry, you are not authorized to use this command!"
        return "Catch em' All: Invalid syntax - use /poke_stat [bank_id]"

    # Randomly creates a pokemon encounter and alerts all available chat channels
    def encounter(self):
        while threading.main_thread().is_alive():
            spawn_time = random.randint(10,20) # 1200,3600

            if self.encounter_exists:
                self.encounter_exists = False
                self.current_encounter = None
                for channel in self.channels:
                    self.bot.send_message(channel, "Catch em' All: Aw, it got away!")
            else:
                self.current_encounter = self.poke_manager.generate_pokemon()
                self.encounter_exists = True
                for channel in self.channels:
                    self.bot.send_message(channel, "Catch em' All: A wild " + self.current_encounter.name + " appeared!")
            sleep(spawn_time)

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "poke_enable":
            if command.chat.id in self.channels:
                return {"type": "message", "message": "This channel is already enabled for encounters."}
            else:
                self.channels.add(command.chat.id)
                return {"type": "message", "message": "Enabled encounters for this channel."}
        elif command.command == "poke_disable":
            if command.chat.id in self.channels:
                self.channels.remove(command.chat.id)
                return {"type": "message", "message": "Disabled encounters for this channel."}
            else:
                return {"type": "message", "message": "Encounters have not been enabled for this channel."}
        elif command.command == "catch":
            return {"type": "message", "message": self.com_catch(command)}
        elif command.command == "poke_list":
            return {"type": "message", "message": self.com_list(command)}
        elif command.command == "poke_release":
            return {"type": "message", "message": self.com_release(command)}
        elif command.command == "poke_stat":
            return {"type": "message", "message": self.com_stat(command)}
        elif command.command == "poke_grant":
            return {"type": "message", "message": self.com_grant(command)}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"poke_enable", "poke_disable", "catch", "poke_list", "poke_release", "poke_stat", "poke_grant"}

    # Returns the name of the plugin
    def get_name(self):
        return "Catch em' All"

    # Run whenever someone types /help catchemall
    def get_help(self):
        return "'/poke_enable' to enable alerts in this channel \n,\
                '/poke_disable' to disable alerts in this channel\n,\
                '/catch' to catch a pokemon \n,\
                '/poke_list' to see pokemon you've caught and their bank location\n,\
                'poke_release [bank_id]' to release a pokemon you've caught\n,\
                'poke_stat [bank_id] to view stats on a pokemon you've caught\n,\
                'poke_grant [user] [pokemon] admin command to grant pokemon"


# Class that handles all operations involving saving and accessing pokemon for individual users
class PokeBank:
    def __init__(self, dir):
        # String containing the directory of the plugin config
        self.dir = dir
        # Dictionary containing keys of users and a list of all pokemon they own
        self.bank = {}
        # Attempts to load 'catchemall/pokebank.file' into self.bank should it exist
        self.load()

    # Stores a given pokemon into a users bank
    # Creates a bank for the user if one doesn't already exist
    def store_mon(self, user, pokemon):
        if user in self.bank.keys():
            self.bank[user].append(pokemon)
            self.save()
        else:
            self.bank[user] = []
            self.bank[user].append(pokemon)
            self.save()

    # Removes and returns a pokemon from a users bank given its location
    # Returns None if the location is out of bounds
    def remove_mon(self, user, location):
        if location < len(self.bank[user]):
            poke = self.bank[user].pop(location)
            self.save()
            return poke
        return None

    # Returns a pokemon obj from the specified location within the list should it exist
    # Returns None if the location is out of bounds
    def get_mon(self, user, location):
        if location < len(self.bank[user]):
            poke = self.bank[user][location]
            return poke
        return None

    # Returns a list of all pokemon in a valid user's bank
    # Returns None if the user does not have a bank
    def user_list(self, user):
        return self.bank[user]

    # Returns true if the user exists in the bank
    def user_exists(self, user):
        if user in self.bank.keys():
            return True
        return False

    # Saves the bank to pokebank.file
    def save(self):
        with open(self.dir + "/pokebank.file", "wb") as f:
            pickle.dump(self.bank, f)
            f.seek(0)
            f.close()

    # Attempts to load an available pokebank.file
    def load(self):
        try:
            if os.path.getsize(self.dir + "/pokebank.file") > 0:
                with open(self.dir + "/pokebank.file", "rb") as f:
                    self.bank = pickle.load(f)
                    f.seek(0)
                    f.close()
            print("Catch em' All: PokeBank file successfully loaded!")
        except FileNotFoundError:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)

            # Ensures that the pokebank file is created.
            with open(self.dir + "/pokebank.file", "w+") as f:
                f.write("")
                f.seek(0)
                f.close()
            print("Catch em' All: No PokeBank file exists, creating a new one.")


# Manages and generates pokemon
class PokemonManager:
    def __init__(self, dir):
        self.dir = dir
        self.pokemon = self.build_set()

    # Attempts to build a dictionary containing all pokemon and their essential data
    def build_set(self):
        data = {}

        try:
            poke_data = json.load(open(os.path.join(self.dir + "/", "pokedex.json")))

            for item in poke_data:
                name = item["ename"]
                attack = item["base"]["Attack"]
                defense = item["base"]["Defense"]
                max_hp = item["base"]["HP"]
                data[name] = {"name" : name, "base_atk" : attack, "base_def" : defense, "base_hp" : max_hp}
            return data

        except NotADirectoryError:
            data["missingno"] = {"name" : "???", "base_atk" : 0, "base_def" : 0, "base_hp" : 1}
            return data

    # Returns True if a specifc pokemon exists
    def find_pokemon(self, name):
        if name in self.pokemon.keys():
            return True
        return False

    # Returns a newly randomly generated pokemon
    def generate_pokemon(self):
        keys = list(self.pokemon.keys())
        key = random.choice(keys)
        poke = self.pokemon[key]
        return Pokemon(poke["name"], poke["base_atk"], poke["base_def"], poke["base_hp"])

    # Returns a specified newly generated pokemon
    def generate_exact_pokemon(self, name):
        poke = self.pokemon[name]
        return Pokemon(poke["name"], poke["base_atk"], poke["base_def"], poke["base_hp"])


# Stores information on a specific pokemon and handles initial generation and increases in stats
class Pokemon:
    def __init__(self, poke_name, base_atk, base_def, base_hp):
        # String Name of the pokemon
        self.name = poke_name
        # Int Attack of the pokemon
        self.attack = base_atk
        # Int Defence of the pokemon
        self.defence = base_def
        # Int Hitpoints of the pokemon
        self.max_hp = base_hp
        # Int The current hitpoints of the pokemon
        self.current_hp = base_hp
        # Bool Flag that determines if the pokemon is fanted or not (if current_hp == 0 this should be True)
        self.is_fainted = False
        # Int Level the pokemon is currently at (levels up at 100 xp)
        self.level = 1
        # Int XP the pokemon currently posseses (resets at 100 xp)
        self.xp = 0
        # Float CP Multiplier
        self.cp_multi = (self.level / 100)
        # Int Combat Power the pokemon posesses (based off its stats)
        self.cp = 0

        # Adds noise to pokemon attributes
        self.add_iv_noise()
        self.calculate_cp()

    # Adds some noise to distinct pokemon attributes
    def add_iv_noise(self):
        self.attack = int((self.attack + random.randint(0,15)) + self.attack * self.cp_multi)
        self.defence = int((self.defence + random.randint(0,15)) + self.defence * self.cp_multi)
        self.max_hp = int((self.max_hp + random.randint(0,15)) + self.max_hp * self.cp_multi)
        self.current_hp = self.max_hp

    # Run every level up to adjust stats
    def update_stats(self):
        self.attack += random.randint(0,3) + (self.attack * self.cp_multi)
        self.defence += random.randint(0,3) + (self.defence * self.cp_multi)
        self.max_hp += random.randint(0,3) + (self.max_hp * self.cp_multi)
        self.xp = self.xp % 100
        self.level += 1
        self.calculate_cp()

    # Calculates the combat power of the pokemon
    def calculate_cp(self):
        self.cp = int((self.attack * (self.defence**.5) * (self.max_hp**.5) * (self.cp_multi)) / 10)

    # Increases xp of this pokemon by the provided amount and checks for a level up
    def grant_xp(self, amount):
        self.xp += amount
        self.check_level_up()

    # Checks if a pokemon is capable of leveling up, if so, it levels it up!
    def check_level_up(self):
        if self.xp >= 100:
            self.update_stats()
            return True
        return False

    def __str__(self):
        message = "Catch em' All: Stats for {}\n".format(self.name)
        message += "HP: {}/{}\n".format(str(self.current_hp), str(self.max_hp))
        message += "CP: {}\n".format(str(self.cp))
        message += "Lv: {}\n".format(str(self.level))
        message += "Xp: {}/{}\n".format(str(self.xp), str(100))
        return message