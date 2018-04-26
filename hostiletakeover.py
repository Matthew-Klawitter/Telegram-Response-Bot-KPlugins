import json

import os
import random
import threading

from libs.honorbank import HonorBank
from plugin import Plugin


def load(data_dir, bot):
    return HostileTakeover(data_dir, bot)


"""
Created by Matthew Klawitter 4/21/2018
Last Updated: 4/26/2018
Version: v1.0.0.0
"""


class HostileTakeover(Plugin):
    def __init__(self, data_dir, bot):
        self.data_dir = data_dir
        self.bot = bot
        self.companies = []

        self.account_manager = HonorBank()
        self.load_companies()
        self.event_management = EventManagement(data_dir)
        # TODO: get this thread working!
        # thread = threading.Thread(43200, self.generate_conditions())
        # thread.setDaemon(True)
        # thread.start()

    def create_company(self, command):
        """
        Charges the user a specified amount of honor and creates a company
        :param command:
        :return String: A response string detailing the command results
        """

        startup_cost = 25000
        commands = command.args.split(" ")
        if len(commands) == 1:
            if self.get_company(commands[0].lower()) is None:
                if self.account_manager.charge(command.user.username, startup_cost):
                    new_company = Company(commands[0].lower(), command.user.username)
                    self.companies.append(new_company)
                    # self.save_companies()
                    return "CafeHT: Successfully created new company {}".format(commands[0])
                return "CafeHT: Unable to create new company. You need {} honor to make a company!".format(startup_cost)
            return "CafeHT: Unable to create new company. A company with this name already exists!"
        return "CafeHT: Invalid command format! Please enter /createcomp [company_name]"

    def check_owner(self, command):
        """
        Get's the name of a company's owner
        :param command:
        :return String: company's owner
        """

        commands = command.args.split(" ")
        if len(commands) == 1:
            company = self.get_company(commands[0].lower())
            if company is not None:
                return "CafeHT: The owner of this company is {}".format(company.owner)
            return "CafeHT: That company does not exist!"
        return "CafeHT: Invalid command format! Please enter /checkowner [company_name]"

    def list_companies(self):
        """
        Creates a detailed response containing the names of all available companies
        :return: a string listing out all available companies
        """

        response = "CafeHT: The following companies are available:\n"
        for company in self.companies:
            response += company.name + "\n"
        return response

    def claim_profits(self, command):
        """
        Pays out all profits to the users invested in a specific company.
        Only the owner of a company may pay out profits.
        Profits are paid out to the owner, and all investors.
        Algorithm is profits * share% * market_mod
        This will be made more efficient at a later time
        """

        commands = command.args.split(" ")
        if len(commands) == 1:
            company = self.get_company(commands[0].lower())
            if company is not None:
                if company.owner == command.user.username:
                    if company.paid_today:
                        profits = company.profits
                        market_mod = 0.0
                        policies = company.policies

                        for condition in self.event_management.current_conditions:
                            for policy in policies:
                                if policy.modifiers.__contains__(condition.name):
                                    market_mod += policy.mod_mc
                                else:
                                    market_mod += policy.default_mc

                        if market_mod < 0:
                            market_mod = 0.0

                        for share_owner in company.shares.keys:
                            shares = company.shares[share_owner]
                            payment = int(profits * (shares / 100) * market_mod)
                            self.account_manager.pay(share_owner, payment)

                        # self.save_companies()
                        return "CafeHT: Payments have been made for the company {}!".format(company.name)
                    return "CafeHT: This company has already paid out today."
                return "CafeHT: Only the company owner can issue this command."
            return "CafeHT: The company {} does not exist!".format(command.args)
        return "CafeHT: Invalid command format! Please enter /claim [company_name]"

    def invest(self, command):
        """
        Invests currency into a company.
        Once certain milestones are hit the company's tier may upgrade.
        :param command: inputs taken from the user
        :return: a string detailing the results of the command
        """
        commands = command.args.split(" ")
        if len(commands) == 2:
            company = self.get_company(commands[0].lower())
            if company is not None:
                try:
                    company.value += int(commands[1])
                    self.account_manager.charge(command.user.username, int(commands[1]))
                    # self.save_companies()
                    return "CafeHT: Invested {} into {} company!".format(int(commands[1]), company.name)
                except ValueError:
                    return "CafeHT: Invalid command format! Please enter /invest [company_name] [amount]"
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /invest [company_name] [amount]"

    def buy_shares(self, command):
        """
        Charges the buyer and transfers a specified amount of shares from a share owner to them
        :param command: inputs taken from the user
        :return: a string detailing the results of the command
        """

        commands = command.args.split(" ")
        if len(commands) == 3:
            company = self.get_company(commands[0].lower())
            if company is not None:
                try:
                    if company.tier >= 4:
                        cost = (company.value / 100) * int(commands[2])
                        if self.account_manager.get_funds(command.user.username) >= cost:
                            if company.transfer_shares(command.user.username, commands[1], int(commands[2])):
                                self.account_manager.charge(command.user.username, cost)
                                self.account_manager.pay(commands[1], int(cost * 0.9))
                                # self.save_companies()
                                return "CafeHT: Transferred shares from {} to {}".format(commands[1],
                                                                                         command.user.username)
                            return "CafeHT: Unable to transfer shares. They do not possess that amount!"
                        return "CafeHT: Unable to transfer shares. You cannot afford {} honor!".format(cost)
                    return "CafeHT: Unable to transfer shares. This company is not yet public at tier 4."
                except ValueError:
                    return "CafeHT: Invalid command format! Please enter /buyshares [company] [person] [amount]"
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /buyshares [company] [person] [amount]"

    def check_share(self, command):
        """
        Checks the value of shares at a specific company
        :param command: inputs taken from user
        :return: a string detailing the results of the command
        """

        commands = command.args.split(" ")
        if len(commands) == 1:
            company = self.get_company(commands[0].lower())
            if company is not None:
                cost = (company.value / 100)
                return "CafeHT: The current value of shares at {} is {} honor.".format(company.name, cost)
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /checkshares [company_name]"

    def market_conditions(self):
        """
        Obtains a description of the current market conditions
        :return: a string describing the current market conditions
        """

        return self.event_management.condition_descriptions()

    def add_policy(self, command):
        """
        Adds a specified policy to a given company
        :param command:
        :return:
        """

        commands = command.args.split(" ")
        if len(commands) == 2:
            company = self.get_company(commands[0].lower())
            if company is not None:
                if command.user.username == company.owner:
                    if self.event_management.policies_list.__contains__(commands[1]):
                        if company.add_policy(commands[1]):
                            return "CafeHT: Successfully added {} policy to this company!".format(commands[1])
                        return "CafeHT: Unable to add policy. It may already be set in this company or policy limit " \
                               "is full "
                    return "CafeHT: Unable to add policy. {} is not a policy.".format(commands[1])
                return "CafeHT: Unable to add policy. You are not the owner of this company."
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /addpol [company_name] [policy_name]"

    def remove_policy(self, command):
        """

        :param command:
        :return:
        """

        commands = command.args.split(" ")
        if len(commands) == 2:
            company = self.get_company(commands[0].lower())
            if company is not None:
                if command.user.username == company.owner:
                    if company.remove_policy(commands[1]):
                        return "CafeHT: Successfully removed {} policy from this company!".format(commands[1])
                    return "CafeHT: Unable to remove policy. It does not exist within this company!"
                return "CafeHT: Unable to remove policy. You are not the owner of this company."
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /rmpol [company_name] [policy_name]"

    def list_policies(self, command):
        """

        :param command:
        :return:
        """

        commands = command.args.split(" ")
        if len(commands) == 1:
            company = self.get_company(commands[0].lower())
            if company is not None:
                response = "CafeHT: The following are policies held by the company:\n"
                for policy in company.policies:
                    response += policy.name + ": " + policy.description + "\n"
                return response
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /listpol [company_name]"

    def all_policies(self):
        """

        :return:
        """

        response = "CafeHT: Here is a list of all policies:\n"
        for policy in self.event_management.policies_list:
            response += policy.name + ", "
        return response

    def get_company(self, name):
        """

        :param name:
        :return:
        """

        for company in self.companies:
            if company.name == name:
                return company
        return None

    def save_companies(self):  # TODO: implement this correctly
        """

        :return:
        """

        with open(self.data_dir + "/" + "companies" + ".json", "w+") as f:
            json.dump(self.companies, f, sort_keys=True, indent=4)
            f.seek(0)
            f.close()

    def load_companies(self):  # TODO: implement this correctly
        """

        :return:
        """

        try:
            if os.path.getsize("/data/companies.json") > 0:
                with open(self.data_dir + "/data/companies.json", "r+") as f:
                    self.companies = json.load(f)
                    f.seek(0)
                    f.close()
        except FileNotFoundError:
            if not os.path.exists(self.data_dir + "/data"):
                os.makedirs(self.data_dir + "/data")

            # Ensure that the account file is created.
            with open(self.data_dir + "/data/companies.json", "w+") as f:
                f.write("")
                f.seek(0)
                f.close()

    def generate_conditions(self):
        """

        :return:
        """

        self.event_management.set_conditions()
        for company in self.companies:
            company.paid_today = False
            # self.save_companies()

    def on_command(self, command):
        """

        :param command:
        :return:
        """

        if command.command == "createcomp":
            return {"type": "message", "message": self.create_company(command)}
        elif command.command == "checkowner":
            return {"type": "message", "message": self.check_owner(command)}
        elif command.command == "listcomp":
            return {"type": "message", "message": self.list_companies()}
        elif command.command == "claim":
            return {"type": "message", "message": self.claim_profits(command)}
        elif command.command == "invest":
            return {"type": "message", "message": self.invest(command)}
        elif command.command == "buyshares":
            return {"type": "message", "message": self.buy_shares(command)}
        elif command.command == "checkshares":  # TODO: issue where you only type /checkshares it prints company does not exist, so check arg len
            return {"type": "message", "message": self.check_share(command)}
        elif command.command == "marketconditions":
            return {"type": "message", "message": self.market_conditions()}
        elif command.command == "addpol":
            return {"type": "message", "message": self.add_policy(command)}
        elif command.command == "rmpol":
            return {"type": "message", "message": self.remove_policy(command)}
        elif command.command == "listpol":
            return {"type": "message", "message": self.list_policies(command)}
        elif command.command == "allpol":
            return {"type": "message", "message": self.all_policies()}

    def get_commands(self):
        return {"createcomp", "checkowner", "listcomp", "claim", "invest", "buyshares", "checkshares",
                "marketconditions", "addpol", "rmpol", "listpol", "allpol"}

    def get_name(self):
        return "Hostile Takeover"

    def get_help(self):
        return "/ \n /"


class Company:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
        self.tier = 0
        self.value = 0
        self.profits = 0
        self.paid_today = False
        self.shares = {owner: 100}
        self.policies = []

    def add_policy(self, policy):
        if len(self.policies) < 3:
            if not self.policies.__contains__(policy):
                self.policies.append(policy)
                return True
            return False
        return False

    def remove_policy(self, policy):
        if self.policies.__contains__(policy):
            self.policies.remove(policy)
            return True
        return False

    def transfer_share(self, buyer, seller, amount):
        if self.shares.keys().__contains__(seller):
            if self.shares[seller] >= amount:
                self.shares[seller] = self.shares[seller] - amount
                self.shares[buyer] = self.shares[buyer] + amount
                self.update_owner()
                return True
            return False
        return False

    def update_owner(self):
        for share_owner in self.shares.keys():
            if self.shares[share_owner] > self.shares[self.owner]:
                self.owner = share_owner

    def update_tier(self):
        if 1000 <= self.value < 3000:
            self.tier = 1
        elif 3000 <= self.value < 9000:
            self.tier = 2
        elif 9000 <= self.value < 27000:
            self.tier = 3
        elif 27000 <= self.value < 54000:
            self.tier = 4
        elif 54000 <= self.value < 81000:
            self.tier = 5
        elif 81000 <= self.value < 243000:
            self.tier = 6
        elif 243000 <= self.value < 729000:
            self.tier = 7
        elif 729000 <= self.value < 2187000:
            self.tier = 8
        elif 2187000 <= self.value < 6561000:
            self.tier = 9
        elif 6561000 <= self.value:
            self.tier = 10


class Policy:
    def __init__(self, name, description, default_market, modded_market, modifiers):
        self.name = name
        self.description = description
        self.default_mc = default_market
        self.mod_mc = modded_market
        self.modifiers = modifiers


class MarketCondition:
    def __init__(self, name, description):
        self.name = name
        self.description = description


class EventManagement:
    def __init__(self, data_dir):
        self.policies_list = []
        self.conditions_list = []
        self.current_conditions = []

        self.parse_policies(self.initialize_json(data_dir, "policies"))
        self.parse_conditions(self.initialize_json(data_dir, "conditions"))
        self.set_conditions()

    @staticmethod
    def initialize_json(data_dir, filename):
        try:
            with open(data_dir + "/data/" + filename + ".json", "r+") as f:
                data = json.load(f)
                f.seek(0)
                f.close()
                return data
        except FileNotFoundError:
            if not os.path.exists(data_dir + "/data"):
                os.makedirs(data_dir + "/data")

            # Ensure that the account file is created.
            with open(data_dir + "/data/" + filename + ".json", "w+") as f:
                f.write("")
                f.seek(0)
                f.close()

    def parse_policies(self, data):
        policies = data["Policies"]
        for policy in policies:
            modifiers = [policy["Mods"][0]["Mod1"], policy["Mods"][0]["Mod2"], policy["Mods"][0]["Mod3"]]
            self.policies_list.append(Policy(policy["Name"].lower(), policy["Description"], policy["Default"],
                                             policy["Modded"], modifiers))

    def parse_conditions(self, data):
        conditions = data["Conditions"]
        for condition in conditions:
            self.conditions_list.append(MarketCondition(condition["Name"], condition["Description"]))

    def set_conditions(self):
        mutable_conditions = list(self.conditions_list)
        drawn_conditions = []

        if len(mutable_conditions) >= 3:
            for x in range(0, 3):
                r = random.randint(0, len(mutable_conditions) - 1)
                drawn_conditions.append(mutable_conditions[r])

        self.current_conditions = drawn_conditions

    def condition_descriptions(self):
        description = self.current_conditions[0].name + " : " + self.current_conditions[0].description + "\n" + \
                      self.current_conditions[1].name + " : " + self.current_conditions[1].description + "\n" + \
                      self.current_conditions[2].name + " : " + self.current_conditions[2].description + "\n"

        return "The following conditions are in effect:\n" + description
