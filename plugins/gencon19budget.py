import csv
import os

from pathlib import Path
from plugin import Plugin

# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return Gencon19Budget(data_dir, bot)

# Name the class the name of your plugin
class Gencon19Budget(Plugin):
    def __init__(self, data_dir, bot):
        self.dir = data_dir
        self.bot = bot
        self.budget = Budget(self.dir)

    def on_command(self, command):
        # This method is called when someone types a '/' and one of the commands returned from the set within the get_commands method in this class
        # command is a Command object found within command_wrappers.py
        if command.command == "gen":
            return {"type":"message", "message": self.budget.view_budget(command.user.username)}
        elif command.command == "genset":
            amount = command.args
            try:
                amount = float(amount)
                amount = round(amount, 2)
                return {"type":"message", "message": self.budget.set_budget(command.user.username, amount)}
            except ValueError:
                return {"type":"message", "message": "The amount you typed is invalid (not a float)"} 
        elif command.command == "gens":
            amount = command.args
            try:
                amount = float(amount)
                amount = round(amount, 2)
                return {"type":"message", "message": self.budget.subtract(command.user.username, amount)}
            except ValueError:
                return {"type":"message", "message": "The amount you typed is invalid (not a float)"}
        elif command.command == "gena":
            amount = command.args
            try:
                amount = float(amount)
                amount = round(amount, 2)
                return {"type":"message", "message": self.budget.add(command.user.username, amount)}
            except ValueError:
                return {"type":"message", "message": "The amount you typed is invalid (not a double)"}

    def get_commands(self):
        # Must return a set of command strings
        return {"gen", "genset", "gens", "gena"}

    def get_name(self):
        # This should return the name of your plugin, perferably the same name as this class
        return "Gen Con 2019 Budget Manager"

    def get_help(self):
        return "Commands:\n" \
                "'/gen' To view budget\n" \
                "'/genset [amount]' To set budget\n" \
                "'/gens [amount]' To subtract amount from budget\n" \
                "'/gena [amount]' To add amount to budget\n" \

class Budget:
    def __init__(self, dir):
        self.dir = dir
        self.budget = self.load()

    def is_user(self, username):
        if username in self.budget.keys():
            return True
        return False

    def view_budget(self, username):
        if self.is_user(username):
            return "Current budget for user {}: ${}".format(username, self.budget[username])
        return self.default()

    def set_budget(self, username, amount):
        self.budget[username] = amount
        self.save()
        return "User: {} Budget: ${}".format(username, amount)

    def subtract(self, username, amount):
        if self.is_user(username):
            self.budget[username] -= amount
            self.save()
            return "Remaining budget for user {}: ${}".format(username, self.budget[username])
        return self.default()

    def add(self, username, amount):
        if self.is_user(username):
            self.budget[username] += amount
            self.save()
            return "Remaining budget for user {}: ${}".format(username, self.budget[username])
        return self.default()

    def default(self):
        return "You have not yet set a budget to view. Please enter one using '/genset [amount]'"

    def save(self):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        with open(self.dir + "/budget.csv", "w") as f:
            for key in self.budget.keys():
                f.write("%s,%s\n"%(key,self.budget[key]))

    def load(self):  
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        
        budget_file = Path(self.dir + "/budget.csv")

        if budget_file.is_file():
            with open(self.dir + "/budget.csv", "r") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                d = {}
                for row in csv_reader:
                    print(row)
                    d[row[0]] = row[1]
                return d
        return {}