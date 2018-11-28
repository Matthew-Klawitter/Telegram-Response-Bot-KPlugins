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
Version: v2.0.0.1
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
        # A BattleManager object that manages player pokemon parties and helper methods to simulate battles
        self.battle_manager = BattleManager(self.dir)
        # A NPCManager that generates random Trainers and pokemon parties for users to fight
        self.npc_manager = NPCManager(self.dir, self.poke_manager)

        # Launches a deamon thread that handles alerts and random encounters
        thread = threading.Thread(target = self.encounter)
        thread.daemon = True
        thread.start()

    # Adds a pokemon to a specific users personal pokemon bank (self.poke_bank)
    def com_catch(self, command):
        if self.check_miss():
            return "Catch em' All: You missed! Darn it was so close!"

        user = command.user.username

        if not self.encounter_exists:
            return "Catch em' All: There is no encounter, check back later!"

        if self.current_encounter == None:
            return "Catch em' All: Sorry " + user + ", you missed your chance!"

        poke = self.current_encounter.pop(0)
        self.poke_bank.store_mon(user, poke)

        if len(self.current_encounter) == 0:
            self.current_encounter = None
            self.encounter_exists = False
        return "Catch em' All: Congrats " + user + " you caught {} (cp:{})!".format(poke.name, str(poke.cp))

    def com_fight(self, command):
        user = command.user.username

        if not self.encounter_exists:
            return "Catch em' All: There is no encounter, check back later!"

        if self.current_encounter == None:
            return "Catch em' All: Sorry " + user + ", you missed your chance!"

        if self.battle_manager.has_party(user):
            battle = Battle(user, "Wild Pokemon")
            party = self.battle_manager.get_party(user)

            response = battle.simulate_battle(party, self.current_encounter)
            self.current_encounter = None
            self.encounter_exists = False
            self.battle_manager.heal_party(party)
            self.poke_bank.save()

            return response + "\n\nRemaining wild pokemon fled!"
        return "Catch em' All: You have not made a party!"

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
                if int(commands[0]) < 0:
                    return "Catch em' All: Please enter a non-negative index value!"
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
                if int(commands[0]) < 0:
                    return "Catch em' All: Please enter a non-negative index value!"
                poke = self.poke_bank.get_mon(user, int(commands[0]))
                if not poke == None:
                    return poke.__str__()
                return "Catch em' All: The location you specified does not exist!"
            return "Catch em' All: You do not possess an account!"
        return "Catch em' All: Invalid syntax - use /poke_stat [bank_id]"

    # A simple implementation of trading
    def com_trade(self, command):
        user = command.user.username
        commands = command.args.split(" ")

        if len(commands) == 2: 
            receiver = commands[0]
            bank_index = commands[1]

            try:
                bank_index = int(bank_index)
            except ValueError:
                return "Catch em' All: Invalid syntax - [bank_id] must be an integer!" 

            if self.poke_bank.user_exists(receiver):
                poke = self.poke_bank.remove_mon(user, int(bank_index))
                
                if not poke == None:
                    self.poke_bank.store_mon(receiver, poke)
                    return "Catch em' All: Traded {} to {}!".format(poke.name, receiver)
                return "Catch em' All: The specified pokemon does not exist in your bank!"
            return "Catch em' All: The specified receiver does not have a bank"
        return "Catch em' All: Invalid syntax - use /poke_trade [user] [bank_id]"

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

    # Forms a pokemon party
    def com_form_party(self, command):
        user = command.user.username
        commands = command.args.split(",")

        if 0 < len(commands) <= 6:
            poke_list = []
            
            for index in list(set(commands)):
                poke = self.poke_bank.get_mon(user, int(index))

                if not poke == None:
                    poke_list.append(poke)
                else:
                    return "Catch em' All: Failed! One or more pokemon do not exist in your bank!"

            if self.battle_manager.form_party(user, poke_list):
                return "Catch em' All: Successfully created the party!"
            return "Catch em' All: Failed to created the party! Pokemon specified must be between 0 and 6!"
        return "Catch em' All: Invalid syntax - use /poke_form_party [id1,id2,id3,etc.]"

    # Views a user's currently set pokemon party
    def com_view_party(self, command):
        user = command.user.username
        return self.battle_manager.view_party(user)
    
    # Posts a request to battle an opponent
    def com_post(self, command):
        user = command.user.username
        commands = command.args.split(" ")

        if len(commands) == 1:
            opponent = commands[0]

            if user == opponent:
                return "Catch em' All: You cannot battle yourself!"

            if self.battle_manager.post_battle(user, opponent):
                response = "Catch em' All: Successfully posted a request to battle {}!\n".format(opponent)
                response += "{} you can use '/poke_accept_battle {}' to accept the battle!".format(opponent, user)
                return response
            return "Catch em' All: Unable to create battle! You have already posted an existing battle"
        return "Catch em' All: Invalid syntax - use /poke_post [opponent_name]"

    # Removes a request to battle an opponent
    def com_rm_post(self, command):
        user = command.user.username
        
        if self.battle_manager.remove_battle(user):
            return "Catch em' All: Successfully removed your posted battle!"
        return "Catch em' All: Unable to remove your posted battle! You have not created one!"

    # Accepts a request to battle an opponent and simulates the battle
    def com_accept_battle(self, command):
        user = command.user.username
        commands = command.args.split(" ")

        if len(commands) == 1:
            challenger = commands[0]
            response = self.battle_manager.accept_battle(user, challenger)
            self.poke_bank.save()
            return response
        return "Catch em' All: Invalid syntax - use /poke_accept_battle [challenger_name]"

    # Randomly creates a pokemon encounter and alerts all available chat channels
    def encounter(self):
        sleep(10)
        while threading.main_thread().is_alive():
            spawn_time = random.randint(300,2400)

            if self.encounter_exists:
                self.encounter_exists = False
                self.current_encounter = None
                for channel in self.channels:
                    self.bot.send_message(channel, "Catch em' All: Aw, the pokemon got away!")
            else:
                rand_spawn = random.randint(1,3)
                response = "Catch em' All: The following wild pokemon appeared:\n"
                spawns = []

                for x in range(rand_spawn):
                    poke = self.poke_manager.generate_pokemon()
                    response += "{} (cp:{})\n".format(poke.name, str(poke.cp))
                    spawns.append(poke)

                self.current_encounter = spawns
                self.encounter_exists = True
                for channel in self.channels:
                    self.bot.send_message(channel, response)
            sleep(spawn_time)

    # Determines if a user missed a catch :B1:
    def check_miss(self):
        r = random.randint(0,100)
        return r <= 8

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
        elif command.command == "fight":
            return {"type": "message", "message": self.com_fight(command)}
        elif command.command == "poke_list":
            return {"type": "message", "message": self.com_list(command)}
        elif command.command == "poke_release":
            return {"type": "message", "message": self.com_release(command)}
        elif command.command == "poke_stat":
            return {"type": "message", "message": self.com_stat(command)}
        elif command.command == "poke_trade":
            return {"type": "message", "message": self.com_trade(command)}
        elif command.command == "poke_grant":
            return {"type": "message", "message": self.com_grant(command)}
        elif command.command == "poke_form_party":
            return {"type": "message", "message": self.com_form_party(command)}
        elif command.command == "poke_view_party":
            return {"type": "message", "message": self.com_view_party(command)}
        elif command.command == "poke_post":
            return {"type": "message", "message": self.com_post(command)}
        elif command.command == "poke_rm_post":
            return {"type": "message", "message": self.com_rm_post(command)}
        elif command.command == "poke_accept_battle":
            return {"type": "message", "message": self.com_accept_battle(command)}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"poke_enable", "poke_disable", "catch", "fight", "poke_list", "poke_release", "poke_stat",\
                "poke_trade", "poke_grant", "poke_form_party", "poke_view_party", "poke_post",\
                "poke_rm_post", "poke_accept_battle"}

    # Returns the name of the plugin
    def get_name(self):
        return "Catch em' All"

    # Run whenever someone types /help catchemall
    def get_help(self):
        return "'/poke_enable' to enable alerts in this channel \n,\
                '/poke_disable' to disable alerts in this channel\n,\
                '/catch' to catch a pokemon \n,\
                '/fight' to fight the current encounter \n,\
                '/poke_list' to see pokemon you've caught and their bank location\n,\
                '/poke_release [bank_id]' to release a pokemon you've caught\n,\
                '/poke_stat [bank_id] to view stats on a pokemon you've caught\n,\
                '/poke_trade [receiver] [bank_id] to trade a pokemon you own\n,\
                '/poke_grant [user] [pokemon] admin command to grant pokemon\n,\
                '/poke_form_party [id1,id2,id3,etc.] to create a pokemon party\n,\
                '/poke_view_party to view a created pokemon party\n,\
                '/poke_post [opponent_name]\n,\
                '/poke_rm_post\n,\
                '/poke_accept_battle [challenger_name]"


# Handles methods to generate and battle npcs
class NPCManager:
    def __init__(self, dir, poke_manager):
        self.dir = dir
        self.poke_manager = poke_manager

    def generate_npc(self, difficulty):
        return NPC(self.generate_name(difficulty), self.generate_party(difficulty))

    def generate_name(self, difficulty):
        prefix = []
        name = []

        if difficulty == 0:
            prefix = ["Youngster", "Bug-Catcher", "Lass", "Lad"]
            name = ["Joey", "Jill", "Bob", "Sally", "Sandy", "Larry"]
        elif difficulty == 1:
            prefix = ["Breeder", "Hiker", "Fisherman", "Coder", "Businessman", "Tuber"]
            name = ["Tom", "Geralt", "Terry", "Mark", "Rowan", "Missy", "Alice", "Sue"]
        elif difficulty == 2:
            prefix = ["Punk", "Guitarist", "Sky-Pirate", "Sailor", "Seafarer", "Challenger", "Principle"]
            name = [""]
        elif difficulty == 3:
            prefix = ["Rocket-Grunt", "Leader", "Gym-Leader", "Ace-Trainer", "Bryce-Look-Alike"]
            name = ["Bill", "Bruce", "Kurt", "Sean", "Trisha", "Jessie", "James", "Watts", "Louise", "Lois", "Elane"]
        elif difficulty == 4:
            prefix = ["Executive", "Director", "Elite", "Chairman"]
            name = ["Giovanni", "Jerry", "Cyrus", "Courtney"]
        elif difficulty == 5:
            prefix = ["Elite-Four", "Frontier-Master", "Rival"]
            name = ["Paul", "Gary", "Lorelei", "Bruno", "Agatha", "Lance"]
        elif difficulty == 6:
            prefix = ["Champion", "Master"]
            name = ["Red", "Blue", "Steven", "Wallace", "Cynthia", "Iris", "Diantha"]
        elif difficulty == 7:
            prefix = ["Developer", "Neuromancer"]
            name = ["Matthew"]
        else:
            prefix = ["Youngster", "Bug-Catcher", "Lass", "Lad"]
            name = ["Joey", "Jill", "Bob", "Sally", "Sandy", "Larry"]

        return random.choice(prefix) + " " + random.choice(name)

    # Generates a random list of pokemon of varying difficulty and returns it
    # Will be refactored in the future
    def generate_party(self, difficulty):
        party = []

        if difficulty == 0: # Levels 1 - 5
            for x in range(2):
                poke = self.poke_manager.generate_pokemon()
                poke.force_level(random.randint(0,5))
                party.append(poke)
        elif difficulty == 1: # Levels 6 - 12
            for x in range(3):
                poke = self.poke_manager.generate_pokemon()
                poke.force_level(random.randint(6,12))
                party.append(poke)
        elif difficulty == 2: # Levels 13 - 18
            for x in range(4):
                poke = self.poke_manager.generate_pokemon()
                poke.force_level(random.randint(13,18))
                party.append(poke)
        elif difficulty == 3: # Levels 19 - 26
            for x in range(4):
                poke = self.poke_manager.generate_pokemon()
                poke.force_level(random.randint(19,26))
                party.append(poke)
        elif difficulty == 4: # Levels 27 - 32
            for x in range(5):
                poke = self.poke_manager.generate_pokemon()
                poke.force_level(random.randint(27,32))
                party.append(poke)
        elif difficulty == 5: # Levels 33 - 40
            for x in range(5):
                poke = self.poke_manager.generate_pokemon()
                poke.force_level(random.randint(33,40))
                party.append(poke)
        elif difficulty == 6: # Levels 41 - 50
            for x in range(6):
                poke = self.poke_manager.generate_pokemon()
                poke.force_level(random.randint(41,50))
                party.append(poke)
        elif difficulty == 7: # Unfair... 9 level 100 pokemon
            poke = self.poke_manager.generate_exact_pokemon("Eevee")
            poke.force_level(99)
            party.append(poke)

            poke = self.poke_manager.generate_exact_pokemon("Espeon")
            poke.force_level(99)
            party.append(poke)

            poke = self.poke_manager.generate_exact_pokemon("Umbreon")
            poke.force_level(99)
            party.append(poke)

            poke = self.poke_manager.generate_exact_pokemon("Sylveon")
            poke.force_level(99)
            party.append(poke)

            poke = self.poke_manager.generate_exact_pokemon("Vaporeon")
            poke.force_level(99)
            party.append(poke)

            poke = self.poke_manager.generate_exact_pokemon("Flareon")
            poke.force_level(99)
            party.append(poke)

            poke = self.poke_manager.generate_exact_pokemon("Jolteon")
            poke.force_level(99)
            party.append(poke)

            poke = self.poke_manager.generate_exact_pokemon("Leafeon")
            poke.force_level(99)
            party.append(poke)

            poke = self.poke_manager.generate_exact_pokemon("Glaceon")
            poke.force_level(99)
            party.append(poke)
        else:
            for x in range(2):
                poke = self.poke_manager.generate_pokemon()
                poke.force_level(random.randint(0,5))
                party.append(poke)
        return party


# Contains information on npc's users can battle
class NPC:
    def __init__(self, name, pokemon_list):
        self.name = name
        self.party = pokemon_list

# Manages pokemon battles and records information on records
class BattleManager:
    def __init__(self, dir):
        self.dir = dir
        self.parties = {}
        self.battles = {}

    # Stores a pokemon party within the dict self.parties, only one party per user
    # Sets the value in the dictionary to a list of 1 to 6 pokemon
    def form_party(self, user, poke_list):
        if 0 < len(poke_list) <= 6:
            self.parties[user] = poke_list
            return True
        return False

    # Returns true if the specified user has created a party
    def has_party(self, user):
        if user in self.parties.keys():
            return True
        return False

    # Returns a string containing all pokemon within a created party if it exists
    def view_party(self, user):
        if self.has_party(user):
            response = "Catch em' All: Here is your current party {}:\n".format(user)
            
            for poke in self.parties[user]:
                response += "{} | cp:{}\n".format(poke.name, str(poke.cp))
            return response
        return "Catch em' All: You have not made a party!"

    # Returns a list containing a user's Pokemon party
    def get_party(self, user):
        if self.has_party(user):
            return self.parties[user]
        return None

    # Posts a request to battle an opponent
    # Only one battle request can be created per user at any given time
    def post_battle(self, user, opponent):
        if not user in self.battles.keys():
            self.battles[user] = Battle(user, opponent)
            return True
        return False

    # Removes a request to battle an opponent
    def remove_battle(self, user):
        if user in self.battles.keys():
            self.battles.pop(user, None)
            return True
        return False

    # Restores a pokemon party to full health
    def heal_party(self, party):
        for poke in party:
            poke.current_hp = poke.max_hp

    # A user accepts a battle request and the battle is then simulated
    def accept_battle(self, user, opponent):
        if opponent in self.battles.keys():
            if self.has_party(user) and self.has_party(opponent):
                battle = self.battles[opponent]

                if battle.opponent == user:
                    # A little confusing since the opponent within a battle object is accepting the challengers battle
                    # The user who made the battle
                    challenger_party = self.parties[opponent]
                    # The user who accepted the battle
                    opponent_party = self.parties[user]
                    # Simulate battle
                    results = battle.simulate_battle(challenger_party, opponent_party)

                    # Heal both parties
                    self.heal_party(challenger_party)
                    self.heal_party(opponent_party)

                    # Remove the battle
                    self.battles.pop(opponent)

                    return results
                return "Catch em' All: You are not the opponent for this battle!"
            return "Catch em' All: Cannot battle! Either you or your opponent has not created a party!"
        return "Catch em' All: A battle with that challenger does not exist!"

# Holds information on battles and simulates them
# challenger is the user who created the battle
# opponent is the user who is being challenged and must choose to accept it
class Battle:
    def __init__(self, challenger, opponent):
        self.challenger = challenger
        self.opponent = opponent

    # Simulates a pokemon battle between two parties
    def simulate_battle(self, challenger_party, opponent_party):
        challenge_cp = int(self.average_cp(challenger_party))
        opponent_cp = int(self.average_cp(opponent_party))
        challenge_index = 0
        opponent_index = 0

        winner = None
        battle_log = "The battle between {} and {} commences!\n".format(self.challenger, self.opponent)

        if challenge_cp > opponent_cp:
            battle_log += "The expected winner is {}\n".format(self.challenger)
        else:
            battle_log += "The expected winner is {}\n".format(self.opponent)

        while challenge_index < len(challenger_party) and opponent_index < len(opponent_party):
            challenge_mon = challenger_party[challenge_index]
            opponent_mon = opponent_party[opponent_index]
            battle_log += "{} sends out {}, while {} sends out {}!\n".format(self.challenger, challenge_mon.name, self.opponent, opponent_mon.name)

            current_attacker, current_defender = self.compare_cp(challenge_mon, opponent_mon)

            while challenge_mon.current_hp > 0 and opponent_mon.current_hp > 0:
                if not self.check_dodge():
                    damage = current_attacker.cp * random.randint(4,6)

                    if self.check_crit():
                        battle_log += "Uh oh, {} is charging its power!\n".format(current_attacker.name)
                        damage *= 2
                    
                    current_defender.current_hp -= damage
                    battle_log += "{} deals {} to {}!\n".format(current_attacker.name, str(damage), current_defender.name)
                else:
                    battle_log += "{} managed to dodge {}'s attack!\n".format(current_defender.name, current_attacker.name)

                # Swap attacker and defender for next turn
                temp = current_defender
                current_defender = current_attacker
                current_attacker = temp
            
            if challenge_mon.current_hp <= 0:
                challenge_mon.current_hp = challenge_mon.max_hp
                cp_xp = challenge_mon.cp
                challenge_index += 1
                battle_log += "{}'s {} fainted! {} gained {} xp!\n".format(self.challenger, challenge_mon.name, opponent_mon.name, str(cp_xp + 5))
            
                if opponent_mon.grant_xp(cp_xp + 5):
                    battle_log += "Woah! {}'s {} leveled up!\n".format(self.opponent, opponent_mon.name)
            else:
                opponent_mon.current_hp = opponent_mon.max_hp
                cp_xp = opponent_mon.cp
                opponent_index += 1
                battle_log += "{}'s {} fainted! {} gained {} xp!\n".format(self.opponent, opponent_mon.name, challenge_mon.name, str(cp_xp + 5))
                
                if challenge_mon.grant_xp(cp_xp + 5):
                    battle_log += "Woah! {}'s {} leveled up!\n".format(self.challenger, challenge_mon.name)

            battle_log += "{} has {} pokemon left, while {} has {} pokemon left!\n\n".format(self.challenger, int(len(challenger_party) - challenge_index), self.opponent, int(len(opponent_party) - opponent_index))

        if opponent_index == len(opponent_party):
            winner = self.challenger
            battle_log += "{} is out of usable pokemon! They blacked out!\n".format(self.opponent)
        else:
            winner = self.opponent
            battle_log += "{} is out of usable pokemon! They blacked out!\n".format(self.challenger)

        battle_log += "The battle has concluded! {} is the winner!".format(winner)
        
        return battle_log

    # Returns the average cp of all pokemon within a list
    def average_cp(self, party):
        total_cp = 0

        for poke in party:
            total_cp += poke.cp

        return total_cp / len(party)

    # Compares two pokemon, returning a tuple that first contains the pokemon with the highest cp
    # and the second containing the pokemon with the lowest cp
    def compare_cp(self, poke1, poke2):
        if poke1.cp > poke2.cp:
            return poke1, poke2
        return poke2, poke1

    # Checks to see if the pokemon successfully deals a critical hit
    def check_crit(self):
        r = random.randint(0,100)
        return r <= 5

    # Checks to see if a pokemon manages to dodge an attack
    def check_dodge(self):
        r = random.randint(0,100)
        return r <= 10
    
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

    # Removes and returns a pokemon obj from a users bank given its location
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
        self.cp_multi = 1 / 100
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
        self.attack += int(random.randint(0,3) + (self.attack * self.cp_multi))
        self.defence += int(random.randint(0,3) + (self.defence * self.cp_multi))
        self.max_hp += int(random.randint(0,3) + (self.max_hp * self.cp_multi))
        self.xp = self.xp % 100
        self.level += 1
        self.calculate_cp()

    # Calculates the combat power of the pokemon
    def calculate_cp(self):
        self.cp = int((self.attack * (self.defence**.5) * (self.max_hp**.5) * (self.cp_multi)) / 10)

    # Increases xp of this pokemon by the provided amount and checks for a level up
    def grant_xp(self, amount):
        self.xp += amount
        return self.check_level_up()

    # Checks if a pokemon is capable of leveling up, if so, it levels it up!
    def check_level_up(self):
        if self.xp >= 100:
            self.update_stats()
            return True
        return False

    # Levels up the pokemon
    # takes int levels - the number of levels to increase the pokemon by
    def force_level(self, levels):
        for x in range(levels):
            self.update_stats()

    def __str__(self):
        message = "Catch em' All: Stats for {}\n".format(self.name)
        message += "HP: {}/{}\n".format(str(self.current_hp), str(self.max_hp))
        message += "CP: {}\n".format(str(self.cp))
        message += "Lv: {}\n".format(str(self.level))
        message += "Xp: {}/{}\n".format(str(self.xp), str(100))
        return message