import json
import os
import random
import urllib
from threading import Timer
from time import sleep

from plugin import Plugin


def load(data_dir):
    return CafeTCG(data_dir)


"""
Created by Matthew Klawitter 11/15/2017
Last Updated: 11/16/2017
Version: v1.0.1.0
"""


class CafeTCG(Plugin):
    def __init__(self, data_dir):
        self.dir = data_dir
        self.cafetcg = {}
        self.cardlist = []

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        self.build_cards()
        self.pack_manager = CardPack(self.cardlist)
        self.card_storage = CardManager(self.dir, self.cardlist)
        self.account_manager = HonorAccount(self.dir, self.cardlist)

        if self.account_manager.load_accounts():
            print("CafeTCG: Accounts successfully loaded")

    def build_cards(self):
        response = urllib.request.urlopen(
            'https://raw.githubusercontent.com/MattKlawitter/Telegram-Response-Bot-KPlugins/dev/Cafe_TCG/Cafe_TCG.json')
        card_data = json.loads(response.read().decode())
        total = len(card_data['Character'])

        if total is not None or total > 0:
            self.cafetcg['total_count'] = total
            self.cafetcg["failure"] = False
        else:
            print("CafeTCG: Uh oh, could not load json! This might be rip!")
            self.cafetcg["failure"] = True

        if not self.cafetcg["failure"]:
            self.parse_cardlist(card_data["Character"], "Character")
            self.parse_cardlist(card_data["Ability"], "Ability")
            self.parse_cardlist(card_data["Item"], "Item")
            self.parse_cardlist(card_data["Location"], "Location")
            self.parse_cardlist(card_data["Argument"], "Argument")
        else:
            print("Failed to load tcg dataset!")
            print("Using backup data... NYI!!!")
            self.card_backup()

    def card_backup(self):
        with open(self.dir + "/" + "cardbackup.txt", "w+") as f:
            f.seek(0)
            f.write("Backup here eventually..." + "There are " + str(self.cafetcg['total_count']) + " cards!")
            f.close()

    def parse_cardlist(self, data_list, card_type):
        for item in data_list:
            card_info = {"type": card_type, "name": item["Info"]["Title"], "id": item["Info"]["ID"],
                         "honor": item["Info"]["Honor"], "cred": item["Info"]["Credibility"],
                         "desc": item["Info"]["Description"], "ability": item["Info"]["Ability"],
                         "faction": item["Info"]["Faction"], "rarity": item["Info"]["Rarity"]}

            card = Card(card_info)
            self.cardlist.append(card)

    def get_card(self, cardname):
        for item in self.cardlist:
            if item.get_name() == cardname:
                return item.long_desc()
        return "That card does not exist!"

    def open_pack(self, command):
        username = command.user.username
        charge_amount = 300

        if not self.card_storage.account_exists(username):
            self.card_storage.create_account(username)

        if self.account_manager.create_account(username):
            print("CafeTCG: Created account for " + username)

        if self.account_manager.charge(username, charge_amount):
            card_pack = self.pack_manager.open_card_pack()

            cards_drawn = "You drew... \n"

            for card in card_pack:
                cards_drawn += "Name: " + card.get_name() + "\n"
                cards_drawn += "Rarity: " + card.get_rarity() + "\n\n"
                self.card_storage.add_card(command.user.username, card)

            self.account_manager.save_accounts()
            return cards_drawn
        return username + ", your account doesn't possess enough funds!"

    def read_card(self, command):
        return self.get_card(command.args)

    def sell_card(self, command):
        username = command.user.username

        if not self.card_storage.account_exists(username):
            self.card_storage.create_account(username)

        if self.account_manager.create_account(username):
            print("CafeTCG: Created account for " + username)

        if self.card_storage.remove_card(command.user.username, command.args):
            value = 0

            for card in self.cardlist:
                if card.get_name() == command.args:
                    value = int(card.get_honor())

            self.account_manager.pay(username, value)
            self.account_manager.save_accounts()
            return "Successfully sold a " + command.args + " for " + str(value) + " honor!"
        return "Failed to sell your " + command.args + ". It might not exist!"

    def get_collection(self, command):
        if not self.card_storage.account_exists(command.user.username):
            self.card_storage.create_account(command.user.username)
        return self.card_storage.get_collection(command.user.username)

    def trade_card(self, command):
        from_user = command.user.username

        try:
            to_user = command.args[:command.args.index(" ")]
            card_name = command.args[command.args.index(" ") + 1:]
        except TypeError:
            return "CafeTCG: Invalid command format! Please enter command in the format: /pay amount @user"

        if not self.card_storage.account_exists(from_user):
            self.card_storage.create_account(from_user)
        if not self.card_storage.account_exists(to_user):
            self.card_storage.create_account(to_user)

        if self.card_storage.remove_card(from_user, card_name):
            self.card_storage.add_card(to_user, card_name)
            return "{} has given a {} to {}!".format(from_user, card_name, to_user)
        return "Unable to send {} to {}. That card doesn't exist!".format(card_name, to_user)

    def check_balance(self, command):
        username = command.user.username

        if self.account_manager.create_account(username):
            print("CafeTCG: Created account for " + username)
        return self.account_manager.get_funds(username)

    # Gosh this method is a mess...
    def make_payment(self, command):
        parts = command.args.split(" ")

        from_user = command.user.username

        try:
            to_user = parts[0]
        except TypeError:
            return "CafeTCG: Invalid command format! Please enter /pay amount @user"

        if not self.card_storage.account_exists(from_user):
            self.card_storage.create_account(from_user)
        if not self.card_storage.account_exists(to_user):
            self.card_storage.create_account(to_user)

        if self.account_manager.create_account(from_user):
            print("CafeTCG: Created account for " + from_user)
        if not self.account_manager.create_account(to_user):
            print("CafeTCG: Created account for " + to_user)

        try:
            if self.account_manager.charge(from_user, int(parts[1])):
                self.account_manager.pay(to_user, int(parts[1]))
                self.account_manager.save_accounts()
                return "{} has paid {} honor to {}!".format(from_user, str(parts[1]), to_user)
        except TypeError:
            return "CafeTCG: Invalid command format! Please enter /pay amount @user"

    def on_command(self, command):
        print(command.command)
        if command.command == "openpack":
            return self.open_pack(command)
        elif command.command == "readcard":
            return self.read_card(command)
        elif command.command == "sellcard":
            return self.sell_card(command)
        elif command.command == "mycollection":
            return self.get_collection(command)
        elif command.command == "tradecard":
            return self.trade_card(command)
        elif command.command == "balance":
            return self.check_balance(command)
        elif command.command == "pay":
            return self.make_payment(command)

    def get_commands(self):
        return {"openpack", "readcard", "sellcard", "mycollection", "tradecard", "balance", "pay"}

    def get_name(self):
        return "Cafe TCG"

    def get_help(self):
        return "/cafetcg"


"""
Stores basic information on cards
"""


class Card:
    def __init__(self, card_info):
        self.card_type = card_info["type"]
        self.card_id = card_info["id"]
        self.name = card_info["name"]
        self.honor = card_info["honor"]
        self.cred = card_info["cred"]
        self.desc = card_info["desc"]
        self.ability = card_info["ability"]
        self.faction = card_info["faction"]
        self.rarity = card_info["rarity"]

    def get_type(self):
        return self.card_type

    def get_id(self):
        return self.card_id

    def get_name(self):
        return self.name

    def get_honor(self):
        return self.honor

    def get_cred(self):
        return self.cred

    def get_desc(self):
        return self.desc

    def get_ability(self):
        return self.ability

    def get_faction(self):
        return self.faction

    def get_rarity(self):
        return self.rarity

    def long_desc(self):
        long_desc = "Type: " + str(self.card_type) + "\n"
        long_desc += "ID: " + str(self.card_id) + "\n"
        long_desc += "Name: " + str(self.name) + "\n"
        long_desc += "Value: " + str(self.honor) + "\n"
        long_desc += "Credibility: " + str(self.cred) + "\n"
        long_desc += "Ability: " + str(self.ability) + "\n"
        long_desc += "Faction: " + str(self.faction) + "\n"
        long_desc += "Rarity: " + str(self.rarity)
        return long_desc


"""
Handles card distribution and odds of obtaining certain cards
"""


class CardPack:
    def __init__(self, card_list):
        self.card_list = card_list
        self.common_list = []
        self.uncommon_list = []
        self.rare_list = []
        self.ultra_rare_list = []

        self.parse_rarity()

    def parse_rarity(self):
        for common in self.card_list:
            if common.get_rarity() == "Common":
                self.common_list.append(common)
        for uncommon in self.card_list:
            if uncommon.get_rarity() == "Uncommon":
                self.uncommon_list.append(uncommon)
        for rare in self.card_list:
            if rare.get_rarity() == "Rare":
                self.rare_list.append(rare)
        for ultra_rare in self.card_list:
            if ultra_rare.get_rarity() == "Ultra-Rare":
                self.ultra_rare_list.append(ultra_rare)

    def draw_card(self, rarity_pack):
        rand = random.randint(0, len(rarity_pack) - 1)
        return rarity_pack[rand]

    def open_card_pack(self):
        card_pack = []
        for x in range(0, 3):
            rand = random.randint(1, 101)

            # 45% odds at common
            if 1 <= rand <= 45:
                card_pack.append(self.draw_card(self.common_list))
            # 35% odds at uncommon
            elif 46 <= rand <= 80:
                card_pack.append(self.draw_card(self.uncommon_list))
            # 16% odds at rare
            elif 81 <= rand <= 96:
                card_pack.append(self.draw_card(self.rare_list))
            # 4%
            else:
                card_pack.append(self.draw_card(self.ultra_rare_list))

        return card_pack


"""
Handles the storage and retrieval of cards a users owns
Users are able to manipulate the cards they own to give them to others
"""


class CardManager:
    def __init__(self, directory, card_list):
        self.dir = directory
        self.card_list = card_list

    def create_account(self, name):
        with open(self.dir + "/" + name + ".json", "w+") as f:
            data = {}

            for item in self.card_list:
                data[item.get_name()] = 0

            json.dump(data, f, sort_keys=True, indent=4)
            f.close()

    # def update_account(self):
        # Outside the scope of baseline. Updates account json format to facilitate new cards

    def account_exists(self, name):
        directory = self.dir + "/" + name + ".json"
        return os.path.isfile(directory) and os.path.getsize(directory) > 0

    def add_card(self, name, card_name):
        with open(self.dir + "/" + name + ".json", "r+") as f:
            data = json.load(f)

            value = data[card_name]
            value += 1
            data[card_name] = value

            f.seek(0)
            json.dump(data, f, sort_keys=True, indent=4)
            f.truncate()
            f.close()
            return True

    def remove_card(self, name, card_name):
        with open(self.dir + "/" + name + ".json", "r+") as f:
            data = json.load(f)

            for card in self.card_list:
                if card.get_name() == card_name:
                    value = data[card.get_name()]
                    if value > 0:
                        value -= 1
                        data[card.get_name()] = value
                        f.seek(0)
                        json.dump(data, f, sort_keys=True, indent=4)
                        f.truncate()
                        f.close()
                        return True
            f.seek(0)
            f.close()
            return False

    def get_collection(self, name):
        with open(self.dir + "/" + name + ".json", "r+") as f:
            data = json.load(f)

            collection = "Here is your collection: \n"

            for card in self.card_list:
                value = data[card.get_name()]

                if value > 0:
                    collection += "Name: " + card.get_name() + "        Amount: " + str(value) + "\n"

            f.seek(0)
            f.close()
            return collection


"""
Handles monetary values for user accounts
Useful for attributing value to the cards
"""


class HonorAccount:
    def __init__(self, directory, card_list):
        self.dir = directory
        self.card_list = card_list
        self.honor_accounts = {}
        self.timer = Timer(10.0, self.pay_day)
        self.timer.start()

    def create_account(self, name):
        if name not in self.honor_accounts:
            self.honor_accounts[name] = 1200
            self.save_accounts()
            return True
        return False

    def remove_account(self, name):
        del self.honor_accounts[name]

    def save_accounts(self):
        with open(self.dir + "/" + "honor" + ".json", "w+") as f:
            json.dump(self.honor_accounts, f, sort_keys=True, indent=4)
            f.seek(0)
            f.close()

    def load_accounts(self):
        directory = self.dir + "/" + "honor" + ".json"
        if os.path.isfile(directory) and os.path.getsize(directory) > 0:
            with open(self.dir + "/" + "honor" + ".json", "r+") as f:
                self.honor_accounts = json.load(f)
                f.seek(0)
                f.close()
            return True
        return False

    def get_funds(self, name):
        return self.honor_accounts[name]

    def pay(self, name, amount):
        self.honor_accounts[name] += amount
        return True

    def charge(self, name, amount):
        if self.honor_accounts[name] > amount:
            self.honor_accounts[name] -= amount
            return True
        return False

    def pay_day(self):
        while True:
            if self.honor_accounts:
                for account in self.honor_accounts:
                    self.honor_accounts[account] += 50
                    self.save_accounts()
            sleep(3600)
