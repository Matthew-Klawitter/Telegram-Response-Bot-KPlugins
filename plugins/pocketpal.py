import datetime
import json
import os
import pickle
import random
import socket
import threading
from libs.honorbank import HonorBank
from enum import Enum
from struct import pack, unpack

from plugin import Plugin
from time import sleep


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return PocketPal(data_dir, bot)


"""
Created by Matthew Klawitter 3/17/2019
Last Updated: 3/18/2019
"""


# Main class of the plugin that handles all commands and interactions
class PocketPal(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data '/pocketpal'
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot
        # Dict composed of users as keys and a Pal obj as a value
        self.pals = {}
        self.load()
        # Handles currency management for users
        self.account_manager = HonorBank()

        # Launches a deamon thread that handles alerts and random encounters
        thread = threading.Thread(target = self.update)
        thread.daemon = True
        thread.start()

    # Checks the status of your pal, viewing stats and health
    def com_check(self, command):
        user = command.user.username

        if user in self.pals.keys():
            return self.pals[user].current_status()
        return "PocketPal: You currently do not own a pal! Use '/pnew [name]' to get one!"
       
    # Feeds your pal a designated food
    def com_feed(self, command):
        user = command.user.username

        if not self.account_manager.account_exists(user):
            self.account_manager.create_account(user)

        if user in self.pals.keys():
            if Food.has_name(command.args):
                food = Food.get_food(command.args)
                pal = self.pals[user]

                if self.account_manager.charge(user, 10):
                    if pal.feed(food):
                        return "PocketPal: Successfully fed your pal! This cost you 10 honor."
                    return "PocketPal: Your pet refused to eat since it is full! This cost you 10 honor!"
                return "PocketPal: Sorry, it costs 10 honor to feed your pet! You lack the neccessary funds..."
            return "PocketPal: That food is currently unavailable."
        return "PocketPal: You currently do not own a pal! Use '/pnew [name]' to get one!"

    # Plays a specific game with your pal, improves happyness
    def com_play(self, command):
        user = command.user.username

        if not self.account_manager.account_exists(user):
            self.account_manager.create_account(user)

        if user in self.pals.keys():
            if Game.has_name(command.args):
                game = Game.get_game(command.args)
                pal = self.pals[user]

                if self.account_manager.charge(user, 20):
                    if pal.play(game):
                        return "PocketPal: Successfully entertained your pal! This cost you 20 honor."
                    return "PocketPal: They don't want to play that! This cost you 20 honor."
                return "PocketPal: Sorry, it costs 20 honor to afford that entertainment! You lack the neccessary funds..."
            return "PocketPal: That game is currently unavailable."
        return "PocketPal: You currently do not own a pal! Use '/pnew [name]' to get one!"

    # Cleans your pal
    def com_clean(self, command):
        user = command.user.username

        if not self.account_manager.account_exists(user):
            self.account_manager.create_account(user)

        if user in self.pals.keys():
            pal = self.pals[user]

            if self.account_manager.charge(user, 5):
                pal.clean_pal()
                return "PocketPal: Successfully cleaned your pal's environment! This cost you 5 honor for supplies."
            return "PocketPal: Sorry, it costs 5 honor to clean your pal's environment! You lack the neccessary funds..."
        return "PocketPal: You currently do not own a pal! Use '/pnew [name]' to get one!"

    # Views an image of your pal
    def com_view(self, command):
        user = command.user.username

        if user in self.pals.keys():
            pal = self.pals[user]
            return pal.status_image
        return None

    # Purchase a new pal if you don't have one
    def com_new(self, command):
        user = command.user.username

        if not self.account_manager.account_exists(user):
            self.account_manager.create_account(user)

        if user in self.pals.keys():
            return "PocketPal: You have already own a pal!"
        if self.account_manager.charge(user, 300):
            self.pals[user] = Pal(command.args, self.dir)
            return "PocketPal: Thank you for adopting a new pal for 300 honor! Be sure to take care of it!"
        return "PocketPal: Sorry! You require at least 300 honor to adopt a pal!"

    # Sells your pal for honor
    def com_sell(self, command):
        user = command.user.username

        if not self.account_manager.account_exists(user):
            self.account_manager.create_account(user)

        if user in self.pals.keys():
            pal = self.pals[user]
            value = 0

            if pal.growth == Growth.child.value:
                value = 10
            elif pal.growth == Growth.teen.value:
                value = 300
            elif pal.growth == Growth.adult.value:
                value = 1200
            elif pal.growth == Growth.ascended.value:
                value = 12000

            del self.pals[user]
            self.account_manager.pay(user, value)
            return "PocketPal: Say goodbye! Payed out {} for your {} (Species: {})".format(value, pal.name, pal.species)
        return "PocketPal: You currently do not own a pal! Use '/pnew [name]' to get one!"

    # Shows a list of purchasable foods
    def com_foods(self):
        response = "The following foods are available:\n"

        for food in Food:
            response += food.name + "\n"
        return response

    # Shows a list of playable games
    def com_games(self):
        response = "The following games are available:\n"

        for game in Game:
            response += game.name + "\n"
        return response

    # Saves all pals
    def save(self):
        with open(self.dir + "/pals.file", "wb") as f:
            pickle.dump(self.pals, f)
            f.seek(0)
            f.close()

    # Loads all pals
    def load(self):
        try:
            if os.path.getsize(self.dir + "/pals.file") > 0:
                with open(self.dir + "/pals.file", "rb") as f:
                    self.pals = pickle.load(f)
                    f.seek(0)
                    f.close()
            print("PocketPal: Pal file successfully loaded!")
        except FileNotFoundError:
            if not os.path.exists(self.dir):
                os.makedirs(self.dir)

            # Ensures that the pokebank file is created.
            with open(self.dir + "/pals.file", "w+") as f:
                f.write("")
                f.seek(0)
                f.close()
            print("PocketPal: No Pal file exists, creating a new one.")
            self.pals = {}

    # Updates status of your pal
    def update(self):
        while threading.main_thread().is_alive():
            for user in self.pals.keys():
                self.pals[user].simulate()

            self.save()
            sleep(300)

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "pcheck":
            return {"type": "message", "message": self.com_check(command)}
        elif command.command == "pfeed":
            return {"type": "message", "message": self.com_feed(command)}
        elif command.command == "pplay":
            return {"type": "message", "message": self.com_play(command)}
        elif command.command == "pclean":
            return {"type": "message", "message": self.com_clean(command)}
        elif command.command == "pview":
            return {"type": "photo", "caption": "", "file_name": self.com_view(command)}
        elif command.command == "pnew":
            return {"type": "message", "message": self.com_new(command)}
        elif command.command == "psell":
            return {"type": "message", "message": self.com_sell(command)}
        elif command.command == "pfoods":
            return {"type": "message", "message": self.com_foods()}
        elif command.command == "pgames":
            return {"type": "message", "message": self.com_games()}
        
    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"pcheck", "pfeed", "pplay", "pclean", "pview", "pnew", "psell", "pfoods", "pgames"}

    # Returns the name of the plugin
    def get_name(self):
        return "PocketPal"

    # Run whenever someone types /help catchemall
    def get_help(self):
        return "'/pcheck' to check status of your pal \n,\
                '/pfeed [food]' to feed your pal some food\n,\
                '/pplay [game]' to play a game with your pal\n,\
                '/pclean' to clean up your pal\n,\
                '/pview' to view your pet\n,\
                '/pnew' to get a new pet\n,\
                '/psell' to sell your pet for honor...\n,\
                '/pfoods' to view purchasable food\n,\
                '/pgames' to view playable games"




class Pal():
    def __init__(self, name, dir):
        self.name = name
        self.age = 0
        self.health = 100
        self.mood = Mood.tame.value
        self.hunger = 100
        self.clean = 100
        self.growth = Growth.child.value
        self.alive = True

        self.species = random.choice(os.listdir(dir + "/assets"))

        self.craving = Food.nothing
        self.desire = Game.nothing
        self.received_attention = False

        self.status_image = dir + "/assets/{}/tame.png".format(self.species)
        self.dir = dir

    def feed(self, food):
        if self.hunger < 100:
            if food == self.craving and food != 0:
                self.hunger += 50
            else:
                self.hunger += 30

            if self.hunger > 100:
                self.hunger = 100

            self.craving = Food.nothing
            return True
        return False

    def play(self, game):
        if game == self.desire and game != 0:
            self.desire = Game.nothing
            self.received_attention = True
            return True
        return False

    def clean_pal(self):
        self.clean = 100
        return True

    def simulate(self):
        if not self.alive:
            return

        if self.health <= 0:
            self.alive = False
            self.status_image = self.dir + "/assets/{}/dead.png".format(self.species)
            return

        self.clean -= 4
        self.hunger -= 2
        self.age += 1
        
        if 75 <= self.hunger < 100:
            self.health += 2
        elif 50 <= self.hunger < 75:
            self.health -= 1
            self.hunger -= 1
        elif 25 <= self.hunger < 50:
            self.health -= 2
            self.mood -= 1
            self.hunger -= 2
        elif 0 <= self.hunger < 25:
            self.health -= 3
            self.mood -= 1
            self.hunger -= 2

        if 95 <= self.clean < 100:
            self.health += 2
        elif 75 <= self.clean < 95:
            self.health += 1
        elif 50 <= self.clean < 75:
            self.health -= 1
            self.mood -= 1
        elif 25 <= self.clean < 50:
            self.health -= 2
            self.mood -= 1
            self.hunger -= 1
        elif 0 <= self.clean < 25:
            self.health -= 3
            self.mood -= 1
            self.hunger -= 1

        if self.received_attention:
            self.mood += 1
        else:
            self.mood -= 1

        if self.mood > 9:
            self.mood = 9
        elif self.mood < 0:
            self.mood = 0

        if self.mood == Mood.elated.value:
            self.health += 3
            self.clean += 1
            self.status_image = self.dir + "/assets/{}/elated.png".format(self.species)
        elif self.mood == Mood.delighted.value:
            self.health += 2
            self.status_image = self.dir + "/assets/{}/delighted.png".format(self.species)
        elif self.mood == Mood.happy.value:
            self.health += 1
            self.status_image = self.dir + "/assets/{}/happy.png".format(self.species)
        elif self.mood == Mood.amused.value:
            self.status_image = self.dir + "/assets/{}/amused.png".format(self.species)
        elif self.mood == Mood.tame.value:
            self.mood += 0
            self.status_image = self.dir + "/assets/{}/tame.png".format(self.species)
        elif self.mood == Mood.tired.value:
            self.hunger -= 1
            self.clean -= 1
            self.status_image = self.dir + "/assets/{}/tired.png".format(self.species)
        elif self.mood == Mood.sad.value:
            self.health -= 1
            self.hunger -= 2
            self.clean -= 3
            self.status_image = self.dir + "/assets/{}/sad.png".format(self.species)
        elif self.mood == Mood.depressed.value:
            self.health -= 2
            self.hunger -= 2
            self.clean -= 2
            self.status_image = self.dir + "/assets/{}/depressed.png".format(self.species)
        elif self.mood == Mood.dejected.value:
            self.health -= 3
            self.hunger -= 3
            self.clean -= 3
            self.status_image = self.dir + "/assets/{}/dejected.png".format(self.species)
        elif self.mood == Mood.defeated.value:
            self.health -= 5
            self.hunger -= 4
            self.clean -= 4
            self.status_image = self.dir + "/assets/{}/defeated.png".format(self.species)

        if self.mood > 9:
            self.mood = 9
        elif self.mood < 0:
            self.mood = 0

        if self.health > 100:
            self.health = 100

        if self.clean > 100:
            self.clean = 100
        elif self.clean < 0:
            self.clean = 0

        if self.hunger > 100:
            self.hunger = 100
        elif self.hunger < 0:
            self.hunger = 0

        if self.age < 288:
            self.growth = Growth.child.value
        elif self.age < 864:
            self.growth = Growth.teen.value
        elif self.age < 2016:
            self.growth = Growth.adult.value
        else:
            self.growth = Growth.ascended.value

        self.craving = Food.rand_food()
        self.desire = Game.rand_game()
        self.received_attention = False

    def current_status(self):
        return "{}'s status:\nSpecies: {}\nAge: {}\nHealth: {}/100\nMood: {}\nHunger: {}/100\nCleanliness: {}/100\nStage: {}\nCraving: {}\nDesire: {}".format(self.name, self.species, self.age, self.health, Mood(self.mood).name, self.hunger, self.clean, Growth(self.growth).name, self.craving.name, self.desire.name)




class Growth(Enum):
    child = 0
    teen = 1
    adult = 2
    ascended = 3

    @classmethod
    def has_name(Growth, name):
        for item in Growth:
            if name == item.name:
                return True
        return False

    @classmethod
    def get_growth(Growth, name):
        for item in Growth:
            if item.name == name:
                return item
        return None




class Mood(Enum):
    defeated = 0
    dejected = 1
    depressed = 2
    sad = 3
    tired = 4
    tame = 5
    amused = 6
    happy = 7
    delighted = 8
    elated = 9

    @classmethod
    def has_name(Mood, name):
        for item in Mood:
            if name == item.name:
                return True
        return False

    @classmethod
    def get_mood(Mood, name):
        for item in Mood:
            if item.name == name:
                return item
        return None




class Food(Enum):
    nothing = 0
    pizza = 1
    fried_chicken = 2
    sushi = 3
    sandwich = 4
    kibble = 5
    water = 6
    steak = 7
    bread = 8
    eggs = 9
    toast = 10
    pasta = 11
    rice = 12
    stirfry = 13
    cake = 14
    sausage = 15
    bacon = 16
    noodles = 17

    @classmethod
    def has_name(Food, name):
        for item in Food:
            if name == item.name:
                return True
        return False

    @classmethod
    def get_food(Food, name):
        for item in Food:
            if item.name == name:
                return item
        return None

    @classmethod
    def rand_food(Food):
        return random.choice(list(Food))




class Game(Enum):
    nothing = 0
    tetris = 1
    puyo = 2
    soccer = 3
    disc_golf = 4
    pandemic = 5
    catan = 6
    hangman = 7
    xbox = 8
    playstation = 9
    switch = 10
    piano = 11
    cello = 12
    viola = 13
    violin = 14
    bass = 15
    movies = 16
    dance = 17

    @classmethod
    def has_name(Game, name):
        for item in Game:
            if name == item.name:
                return True
        return False

    @classmethod
    def get_game(Game, name):
        for item in Game:
            if item.name == name:
                return item
        return None

    @classmethod
    def rand_game(Game):
        return random.choice(list(Game))
