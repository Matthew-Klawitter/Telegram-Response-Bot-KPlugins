import datetime
import json
import os
import urllib

from plugin import Plugin


def load(data_dir):
    return HonorFight(data_dir)


"""
Created by Matthew Klawitter 9/27/2017
"""


class HonorFight(Plugin):
    def __init__(self, data_dir):
        self.dir = data_dir
        self.honorfight = {}

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

    def add_user(self, name):
        with open(self.dir + '/' + name + '.txt', 'w') as f:
            f.write(str(0))
            f.close()

    def add_honor(self, name, amount):
        with open(self.dir + '/' + name + '.txt', 'w') as f:
            f.seek(0)
            f.write(str(self.get_honor(name) + amount))

    def get_honor(self, name):
        with open(self.dir + '/' + name + '.txt', 'r') as f:
            return int(f.read())

    def file_exists(self, directory):
        return os.path.isfile(directory) and os.path.getsize(directory) > 0

    def issue_challenge(self, command):
        # date = datetime.date.today().strftime('%m/%d/%Y')
        return command.user.username + " has challenged " + command.mention + " to a fight!"

    def check_honor(self, command):
        if self.file_exists(self.dir + '/' + command.user.username + '.txt'):
            honor = self.get_honor(command.user.username)
            return command.user.first_name + " has " + str(honor) + " honor!"
        else:
            self.add_user(command.user.username)
            return self.check_honor(command)

    def send_honor(self, command):
        return command.user.username + " has challenged " + command.mention + " to a fight!"

    def on_command(self, command):
        if command.command == "challenge":
            return self.issue_challenge(command)
        elif command.command == "honor":
            return self.check_honor(command)
        elif command.command == "sendhonor":
            return self.send_honor(command)

    def get_commands(self):
        return {"challenge", "honor", "sendhonor"}

    def get_name(self):
        return "Honor Fight"

    def get_help(self):
        return "/challenge @name, /honor @name, /sendhonor @name"
