import json
import os
import pickle
import random
import threading
from time import sleep

from libs.honorbank import HonorBank
from plugin import Plugin


def load(data_dir, bot):
    return HostileTakeover(data_dir, bot)


"""
Created by Matthew Klawitter 4/21/2018
Last Updated: 5/4/2018
Version: v1.1.1.1
"""


class HostileTakeover(Plugin):
    def __init__(self, data_dir, bot):
        self.data_dir = data_dir
        self.bot = bot
        self.companies = []

        self.account_manager = HonorBank()
        self.load_companies()
        self.event_management = EventManagement(data_dir)

        thread = threading.Thread(target = self.generate_conditions)  # runs for 43200 seconds
        thread.daemon = True
        thread.start()

    def create_company(self, command):
        """
        Charges the user a specified amount of honor and creates a company
        :param command:
        :return String: A response string detailing the command results
        """

        startup_cost = 25000
        commands = command.args.split(" ")
        if len(commands) == 1:
            if self.get_company(commands[0].lower()) is None and not commands[0] == "":
                if self.account_manager.charge(command.user.username, startup_cost):
                    self.account_manager.save_accounts()
                    new_company = Company(commands[0].lower(), command.user.username)
                    self.companies.append(new_company)
                    self.save_companies()
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
                    if not company.paid_today:
                        profits = company.profits
                        market_mod = 1.0
                        policies = company.policies

                        for condition in self.event_management.current_conditions:
                            for policy in policies:
                                if policy.modifiers.__contains__(condition.name):
                                    market_mod += policy.mod_mc
                                else:
                                    market_mod += policy.default_mc

                        if market_mod < 0:
                            market_mod = 0.0

                        response = "CafeHT: The following amounts have been paid out for {}:\n".format(company.name)
                        for share_owner in company.shares.keys():
                            shares = company.shares[share_owner]
                            payment = int(profits * (shares / 100) * market_mod)
                            response += "{} : {}".format(share_owner, str(payment))
                            self.account_manager.pay(share_owner, payment)

                        company.profits = 0
                        company.paid_today = True
                        self.save_companies()
                        return response
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
                    company.profits += (int(commands[1]) / 5)

                    if self.account_manager.charge(command.user.username, int(commands[1])):
                        company.update_tier()
                        self.save_companies()
                        return "CafeHT: Invested {} into {} company!".format(int(commands[1]), company.name)
                    return "CafeHT: You do not possess {} honor to invest!".format(int(commands[1]))
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
                                if self.account_manager.charge(command.user.username, cost):
                                    self.account_manager.pay(commands[1], int(cost * 0.9))
                                    self.save_companies()
                                    return "CafeHT: Transferred shares from {} to {}".format(commands[1],
                                                                                             command.user.username)
                                return "CafeHT: Unable to transfer shares. Buyer does not have {} honor.".format(cost)
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
                cost = int(company.value / 100)
                return "CafeHT: The current value of shares at {} is {} honor.\n".format(company.name, str(cost)) + \
                       company.share_description()
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
        Adds a specified policy to a given company (up to three policies per company)
        :param command: input providing the company name and policy name
        :return: a string detailing the results of the command
        """

        commands = command.args.split(" ")
        if len(commands) == 2:
            company = self.get_company(commands[0].lower())
            if company is not None:
                if command.user.username == company.owner:
                    for policy in self.event_management.policies_list:
                        if policy.name == commands[1].lower():
                            if company.add_policy(policy):
                                self.save_companies()
                                return "CafeHT: Successfully added {} policy to this company!".format(commands[1])
                            return "CafeHT: Unable to add policy. It may already be set in this company or policy " \
                                   "limit is full "
                    return "CafeHT: Unable to add policy. {} is not a policy.".format(commands[1])
                return "CafeHT: Unable to add policy. You are not the owner of this company."
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /addpol [company_name] [policy_name]"

    def remove_policy(self, command):
        """
        Removes a specific policy from a given company.
        Only removes a policy if it possesses the inputted policy
        :param command: input providing the company name and policy name
        :return: a string detailing the results of the command
        """

        commands = command.args.split(" ")
        if len(commands) == 2:
            company = self.get_company(commands[0].lower())
            if company is not None:
                if command.user.username == company.owner:
                    if company.remove_policy(commands[1]):
                        self.save_companies()
                        return "CafeHT: Successfully removed {} policy from this company!".format(commands[1])
                    return "CafeHT: Unable to remove policy. It does not exist within this company!"
                return "CafeHT: Unable to remove policy. You are not the owner of this company."
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /rmpol [company_name] [policy_name]"

    def list_policies(self, command):
        """
        Lists all policies held by a company (up to three, some may be blank)
        :param command: input providing the company name
        :return: a string detailing the results of the command
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
        Lists all policies that can be held by a company
        :return: a string containing a list of all policies
        """

        response = "CafeHT: Here is a list of all policies:\n"
        for policy in self.event_management.policies_list:
            response += policy.name + ", "
        return response

    def get_tier(self, command):
        """
        Finds the tier of a specified company
        :param command: input providing the company name
        :return: a string detailing the tier of a valid company
        """

        commands = command.args.split(" ")
        if len(commands) == 1:
            company = self.get_company(commands[0].lower())
            if company is not None:
                return "CafeHT: The company is currently at tier {}!".format(company.tier)
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /comptier [company_name]"

    def get_value(self, command):
        """
        Finds the value of a specific company
        :param command: input providing the company name
        :return: a string detailing the value of a valid company
        """

        commands = command.args.split(" ")
        if len(commands) == 1:
            company = self.get_company(commands[0].lower())
            if company is not None:
                return "CafeHT: The company value is currently {}!".format(company.value)
            return "CafeHT: The company {} does not exist!".format(commands[0])
        return "CafeHT: Invalid command format! Please enter /compvalue [company_name]"

    def get_company(self, name):
        """
        Attempts to find a company within self.companies that has
        a designated name
        :param name: the name of the company
        :return: the company object if it is found or None otherwise
        """

        for company in self.companies:
            if company.name == name:
                return company
        return None

    def save_companies(self):
        """
        Saves all companies contained within self.companies into a file
        """

        with open(self.data_dir + "/data/" + "companies" + ".file", "wb") as f:
            pickle.dump(self.companies, f)
            f.seek(0)
            f.close()

    def load_companies(self):
        """
        Loads a list of all companies contained within a file into self.companies
        """

        try:
            if os.path.getsize(self.data_dir + "/data/companies.file") > 0:
                with open(self.data_dir + "/data/companies.file", "rb") as f:
                    self.companies = pickle.load(f)
                    if not isinstance(self.companies, list):  # I'm horrible... I used isinstance...
                        list(self.companies)
                    f.seek(0)
                    f.close()
        except FileNotFoundError:
            if not os.path.exists(self.data_dir + "/data"):
                os.makedirs(self.data_dir + "/data")

            # Ensures that the account file is created.
            with open(self.data_dir + "/data/companies.file", "w+") as f:
                f.write("")
                f.seek(0)
                f.close()

    def generate_conditions(self):
        """
        Runs every 12 hours.
        Generates new market conditions and resets company payout.
        """

        while threading.main_thread().is_alive():
            self.event_management.set_conditions()
            for company in self.companies:
                company.paid_today = False
                company.profits += company.value
            self.save_companies()
            sleep(43200)

    def on_command(self, command):
        if command.command == "createcomp":
            return {"type": "message", "message": self.create_company(command)}
        elif command.command == "compowner":
            return {"type": "message", "message": self.check_owner(command)}
        elif command.command == "listcomp":
            return {"type": "message", "message": self.list_companies()}
        elif command.command == "claim":
            return {"type": "message", "message": self.claim_profits(command)}
        elif command.command == "invest":
            return {"type": "message", "message": self.invest(command)}
        elif command.command == "buyshares":
            return {"type": "message", "message": self.buy_shares(command)}
        elif command.command == "checkshares":
            return {"type": "message", "message": self.check_share(command)}
        elif command.command == "mc":
            return {"type": "message", "message": self.market_conditions()}
        elif command.command == "addpol":
            return {"type": "message", "message": self.add_policy(command)}
        elif command.command == "rmpol":
            return {"type": "message", "message": self.remove_policy(command)}
        elif command.command == "listpol":
            return {"type": "message", "message": self.list_policies(command)}
        elif command.command == "allpol":
            return {"type": "message", "message": self.all_policies()}
        elif command.command == "comptier":
            return {"type": "message", "message": self.get_tier(command)}
        elif command.command == "compvalue":
            return {"type": "message", "message": self.get_value(command)}

    def get_commands(self):
        return {"createcomp", "compowner", "listcomp", "claim", "invest", "buyshares", "checkshares",
                "mc", "addpol", "rmpol", "listpol", "allpol", "comptier", "compvalue"}

    def get_name(self):
        return "Hostile Takeover"

    def get_help(self):
        return "/createcomp [company_name] \n /compowner [company_name] \n /listcomp \n /claim [company_name] \n " \
               "/invest [company_name] [amount] \n /buyshares [company] [person] [amount] \n /checkshares" \
               "[company_name] \n /mc \n /addpol [company_name] [policy_name] \n /rmpol [company_name] [policy_name]" \
               "\n /listpol [company_name] \n /allpol \n /comptier [company_name] \n /compvalue [company_name] \n "


class Company:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
        self.tier = 0
        self.value = 0
        self.profits = 1000
        self.paid_today = False
        self.shares = {owner: 100}
        self.policies = []

    def add_policy(self, policy):
        """
        Adds a policy object to self.policies (up to three at a time)
        :param policy: policy to be added
        :return: True if a policy is added
        """

        if len(self.policies) < 3:
            if not self.policies.__contains__(policy):
                self.policies.append(policy)
                return True
            return False
        return False

    def remove_policy(self, policy_name):
        """
        Removes a policy object from self.policies
        :param policy_name: Name of the policy to be removed
        :return: True if a policy is removed
        """

        for policy in self.policies:
            if policy.name == policy_name:
                self.policies.remove(policy)
                return True
        return False

    def transfer_share(self, buyer, seller, amount):
        """
        Moves shares from one person to another
        :param buyer: name of user to add shares to
        :param seller: name of user to remove shares from
        :param amount: amount of shares to move
        :return: True if shares are successfully transferred
        """

        if self.shares.keys().__contains__(seller):
            if self.shares[seller] >= amount:
                self.shares[seller] = self.shares[seller] - amount
                self.shares[buyer] = self.shares[buyer] + amount
                self.update_owner()
                return True
            return False
        return False

    def update_owner(self):
        """
        Updates the owner of this company if a new user has a majority in the shares owned
        """

        for share_owner in self.shares.keys():
            if self.shares[share_owner] > self.shares[self.owner]:
                self.owner = share_owner

    def update_tier(self):
        """
        Updates the tier of this company based on the amount of value it holds
        """

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

    def share_description(self):
        """
        A description containing all users that own shares in this company and the amount of shares they own
        :return: String description containing users that own shares and the amount they own
        """
        description = "The following people own shares in this company:\n"
        for owner in self.shares.keys():
            description += owner + ": " + str(self.shares[owner])

        return description


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
        """
        Loads json for policies and market conditions.
        Creates a file if one isn't found
        :param data_dir: directory data is held
        :param filename: file to be loaded
        :return: data loaded from json file
        """

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
        """
        Parses policies from json data into a list of Policy objects
        :param data: json data to be parsed
        """
        policies = data["Policies"]
        for policy in policies:
            modifiers = [policy["Mods"][0]["Mod1"].lower(), policy["Mods"][0]["Mod2"].lower(),
                         policy["Mods"][0]["Mod3"].lower()]
            self.policies_list.append(Policy(policy["Name"].lower(), policy["Description"], policy["Default"],
                                             policy["Modded"], modifiers))

    def parse_conditions(self, data):
        """
        Parses market conditions from json data into a list of MarketCondition objects
        :param data: json data to be parsed
        """

        conditions = data["Conditions"]
        for condition in conditions:
            self.conditions_list.append(MarketCondition(condition["Name"].lower(), condition["Description"]))

    def set_conditions(self):
        """
        Sets the current market conditions (picks three conditions from self.conditions_list without replacement)
        """
        mutable_conditions = list(self.conditions_list)
        drawn_conditions = []

        if len(mutable_conditions) >= 3:
            for x in range(0, 3):
                r = random.randint(0, len(mutable_conditions) - 1)
                drawn_conditions.append(mutable_conditions[r])

        self.current_conditions = drawn_conditions

    def condition_descriptions(self):
        """
        Creates and organized string containing information on current market conditions)
        :return: String describing conditions that are in effect
        """
        description = self.current_conditions[0].name + " : " + self.current_conditions[0].description + "\n" + \
                      self.current_conditions[1].name + " : " + self.current_conditions[1].description + "\n" + \
                      self.current_conditions[2].name + " : " + self.current_conditions[2].description + "\n"

        return "The following conditions are in effect:\n" + description
