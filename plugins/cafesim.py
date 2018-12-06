import datetime
import os
import random
import socket
import threading
from struct import pack, unpack
from enum import Enum

from plugin import Plugin
from time import sleep


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return CafeSim(data_dir, bot)


"""
Created by Matthew Klawitter 12/5/2018
Last Updated: 12/5/2018
Version: v0.0.0.0
"""


# Main class of the plugin that handles all commands and interactions
class CafeSim(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data '/catchemall'
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot
        # A set containing all channels in which to send alerts to
        self.channels = set()
        # An object containing actions users can perform
        self.action_manager = ActionManager()
        # A dictionary containing the current role a user is set
        self.roles = {}
        # A dictionary that uses an action name as a key and stores a requirement
        self.current_action = {}
        # Flag determining if the current action was successfully performed
        self.action_performed = False

        # Launches a deamon thread that handles alerts and random encounters
        thread = threading.Thread(target = self.game_loop)
        thread.daemon = True
        thread.start()

    def com_role(self, command):
        user = command.user.username
        role = command.args

        if Role.has_value(role):
            self.roles[user] = Role.role
            return "CafeSim: {} is now a {}!".format(user, role)
        return "CafeSim: The role '{}' does not exist!".format(role)

    def com_perform(self, command):


    def game_loop(self):
        while threading.main_thread().is_alive():
            start_time = random.randint(10,20) # The amount of time until the next game begins
            sleep(start_time)
            self.start_game()

    def start_game(self):
        action_queue = Queue(10)
        roles = set()

        for x in range(10)
            action = self.action_manager.pick_action()
            action_queue.put(action)
            roles.add(action.role.name)

        response = "CafeSim: It's time to start a shift!\n The following roles will be necessary:\n"

        for role in roles:
            response += "{}".format(role)

        self.message_channels(response)
        sleep(10)

        self.message_channels("CafeSim: Here we go!")

        while not action_queue.empty():
            action = action_queue.get()
            req = random.choice(action.requirements)

            # TODO: Figure out a way to store the action.name, the req, and the required role! or just add self.required_role as a var
            self.current_action[action.name] = req
            self.action_performed = False

            self.message_channels(action.trigger_message + "\n Perform /cs_perform {} {}".format(action.name, req))

            sleep(20)

            if self.action_performed:
                self.message_channels("Very good work!")
            else:
                self.message_channels("Terrible work! Your pay's been docked!")
            sleep(5)

        self.message_channels("Good work everyone the shift is over! Time to get paid! See you again soon!")


    def message_channels(self, message):
        for channel in self.channels:
            self.bot.send_message(channel, message)

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "cs_enable":
            if command.chat.id in self.channels:
                return {"type": "message", "message": "This Cafe is already open for business."}
            else:
                self.channels.add(command.chat.id)
                return {"type": "message", "message": "The Cafe is now open."}
        elif command.command == "cs_disable":
            if command.chat.id in self.channels:
                self.channels.remove(command.chat.id)
                return {"type": "message", "message": "The Cafe is now close."}
            else:
                return {"type": "message", "message": "This Cafe has not been opened for business."}
        elif command.command == "cs_role":
            return {"type": "message", "message": self.com_role(command)}
        elif command.command == "cs_perform":
            return {"type": "message", "message": self.com_perform(command)}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"cs_enable", "cs_disable", "cs_role", "cs_perform"}

    # Returns the name of the plugin
    def get_name(self):
        return "CafeSim"

    # Run whenever someone types /help cafesim
    def get_help(self):
        return "'/cs_enable' to enable the game in this channel \n,\
                '/cs_disable' to disable the game in this channel\n,\
                '/cs_role [role_name]' to become a role\n,\
                '/cs_perform [action] [requirement]' to perfrom an action"


class ActionManager:
    def __init__(self):
        self.actions = self.build_actions()

    def build_actions(self):
        return {
            "wait" : Action("wait", "A customer is ready to order! Go wait on them!", ["John", "Jessie", "James", "Jackie"], Role.server, .2),
            "brew" : Action("brew", "The customer wants a coffee! Go brew one!", ["espresso", "mocha"], Role.barista, .1)
            "clean" : Action("clean", "There's a mess on the floor! Go clean it!", ["spill", "trash"], Role.cleaner, .1)
        }
        
    def pick_action(self):
        key = random.choice(self.actions.keys())
        return self.actions[key]

    def action_exists(self, action_name):
        return action_name in self.actions.keys()

    def action_list(self):
        return self.actions.keys()


class Action:
    def __init__(self, action_name, trigger_message, requirements, role, value):
        self.action_name = action_name
        self.trigger_message = trigger_message
        self.requirements = requirements
        self.role = role
        self.value = value


class Role(Enum):
    server = 0
    barista = 1
    cleaner = 2

    @classmethod
    def has_value(Role, value):
        return any(value == item.value for item in Role)