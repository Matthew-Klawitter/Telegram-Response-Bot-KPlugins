import datetime
import os
import pickle
import random
import socket
import threading
from struct import pack, unpack

from plugin import Plugin
from time import sleep


def load(data_dir, bot):
    return CatchEmAll(data_dir, bot)


"""
Created by Matthew Klawitter 11/19/2018
Last Updated: 11/20/2018
Version: v1.0.0.0
"""


class CatchEmAll(Plugin):
    def __init__(self, data_dir, bot):
        self.dir = data_dir
        self.bot = bot
        self.channels = set()
        self.pokemon = self.build_encounters()
        self.pokebank = {}
        self.encounter_exists = False
        self.current_encounter = ""
        self.load()

        thread = threading.Thread(target = self.encounter)
        thread.daemon = True
        thread.start()

    # Builds a list containting all known pokemon
    def build_encounters(self):
        encounters = []

        with open(self.dir + "/pokemon.txt", "r") as f:
            f.seek(0)

            for line in f:
                encounters.append(line.strip())
            
            f.close()

        return encounters

    # Returns a random pokemon from list self.pokemon
    def pick_encounter(self):
        return self.pokemon[random.randint(0, len(self.pokemon))]

    # Adds a pokemon to a specific users personal pokemon bank (dict)
    def catch(self, command):
        user = command.user.username

        if self.current_encounter == "":
            return "Sorry " + user + ", you missed your chance!"

        if user in self.pokebank.keys():
            bank = self.pokebank[user]

            if self.current_encounter in bank.keys():
                bank[self.current_encounter] += 1
            else:
                bank[self.current_encounter] = 1

            self.current_encounter = ""
            self.encounter_exists = False
            self.save()
            return "Congrats " + user + " you caught the pokemon!"
        else:
            self.pokebank[user] = {}
            return self.catch(command)

    # Lists all pokemon within a user's pokemon bank (dict) should they exist
    def bank_list(self, command):
        user = command.user.username

        if user in self.pokebank.keys():
            bank = self.pokebank[user]
            message = user + "'s PokeBank Contents\n"

            for pokemon in bank.keys():
                message += pokemon + ":" + str(bank[pokemon]) + "\n"
            return message
        else:
            return user + " you have not caught any pokemon!"

    # Saves the pokemon bank to pokebank.file
    def save(self):
        with open(self.dir + "/pokebank.file", "wb") as f:
            pickle.dump(self.pokebank, f)
            f.seek(0)
            f.close()

    # Attempts to load an available pokebank.file
    def load(self):
        try:
            if os.path.getsize(self.dir + "/pokebank.file") > 0:
                with open(self.dir + "/pokebank.file", "rb") as f:
                    self.pokebank = pickle.load(f)
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

    # Randomly creates a pokemon encounter and alerts all available chat channels
    def encounter(self):
        while threading.main_thread().is_alive():
            r = random.randint(1200,3600)

            if self.encounter_exists:
                self.encounter_exists = False
                self.current_encounter = ""
                for channel in self.channels:
                    self.bot.send_message(channel, "Aw, it got away!")
            else:
                self.current_encounter = self.pick_encounter()
                self.encounter_exists = True
                for channel in self.channels:
                    self.bot.send_message(channel, "A wild " + self.current_encounter + " appeared!")
            sleep(r)

    def on_command(self, command):
        if command.command == "enablepokemon":
            if command.chat.id in self.channels:
                return {"type": "message", "message": "This channel is already enabled for encounters."}
            else:
                self.channels.add(command.chat.id)
                return {"type": "message", "message": "Enabled encounters for this channel."}
        elif command.command == "disablepokemon":
            if command.chat.id in self.channels:
                self.channels.remove(command.chat.id)
                return {"type": "message", "message": "Disabled encounters for this channel."}
            else:
                return {"type": "message", "message": "Encounters have not been enabled for this channel."}
        elif command.command == "catch":
            return {"type": "message", "message": self.catch(command)}
        elif command.command == "catchlist":
            return {"type": "message", "message": self.bank_list(command)}

    def get_commands(self):
        return {"enablepokemon", "disablepokemon", "catch", "catchlist"}

    def get_name(self):
        return "Catch em' All"

    def get_help(self):
        return "'/enablepokemon', '/disablepokemon', '/catch' to catch a pokemon \n '/list' to see pokemon you've caught"