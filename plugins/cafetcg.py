import json
import os
import random

from libs.honorbank import HonorBank
from plugin import Plugin


def load(data_dir, bot):
    return CafeTCG(data_dir, bot)


"""
Created by Matthew Klawitter 11/15/2017
Last Updated: 11/22/2017
Version: v2.2.2.1
"""


class CafeTCG(Plugin):
    def __init__(self, data_dir, bot):
        self.bot = bot
        self.dir = data_dir
        self.cafetcg = {}
        self.cardlist = []

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        self.build_cards()
        self.pack_manager = PackManager(self.cardlist)
        self.card_storage = CardManager(self.dir, self.cardlist)
        self.card_storage.update_accounts()
        self.account_manager = HonorBank()

    # Builds cards by requesting json data
    def build_cards(self):
        try:
            for file in os.listdir(self.dir + "/" + "data"):
                if file.endswith(".json"):
                    card_data = json.load(open(os.path.join(self.dir + "/" + "data", file)))
                    self.parse_cardlist(card_data["Character"], "Character")
                    self.parse_cardlist(card_data["Ability"], "Ability")
                    self.parse_cardlist(card_data["Item"], "Item")
                    self.parse_cardlist(card_data["Location"], "Location")
                    self.parse_cardlist(card_data["Argument"], "Argument")
        except NotADirectoryError:
            print("Yeah I should do something here")  # TODO: Implement

    # Parses and fills a list with card objects
    def parse_cardlist(self, data_list, card_type):
        for item in data_list:
            card_info = {"type": card_type, "name": item["Info"]["Title"], "set": item["Info"]["Set"],
                         "id": item["Info"]["ID"], "honor": item["Info"]["Honor"], "cred": item["Info"]["Credibility"],
                         "desc": item["Info"]["Description"], "ability": item["Info"]["Ability"],
                         "faction": item["Info"]["Faction"], "rarity": item["Info"]["Rarity"]}

            card = Card(card_info)
            self.cardlist.append(card)

    # Returns a card object based on a card name
    def get_card(self, cardname):
        for item in self.cardlist:
            if item.name == cardname:
                return item
        return None

    # Opens a pack of cards, charging the user, and adding cards to their collection
    def open_pack(self, command):
        charge_amount = 300

        if len(command.args.split(" ")) < 1 or command.args == "":
            return "CafeTCG: Invalid command format! Please enter /booster [pack_name]"
        elif self.pack_manager.pack_exists(command.args):
            pack_name = command.args
        else:
            return "CafeTCG: Invalid pack name! Please enter /packs to see a list of available packs."

        if self.account_manager.charge(command.user.username, charge_amount):
            card_pack = self.pack_manager.open_pack(pack_name)
            cards_drawn = "You spent 300 honor and drew... \n"

            for card in card_pack:
                cards_drawn += "Name: " + card.name + "\n"
                cards_drawn += "Rarity: " + card.rarity + "\n\n"
                self.card_storage.add_card(command.user.username, card.name)
            self.account_manager.save_accounts()

            return cards_drawn
        return command.user.username + ", your account doesn't possess enough funds!"

    # Reads a card off the card list
    def read_card(self, command):
        return self.get_card(command.args).long_desc()

    # Sells a card to obtain honor
    def sell_card(self, command):
        if self.card_storage.remove_card(command.user.username, command.args):
            value = self.get_card(command.args).honor

            self.account_manager.pay(command.user.username, value)
            self.account_manager.save_accounts()
            return "Successfully sold a " + command.args + " for " + str(value) + " honor!"
        return "Failed to sell your " + command.args + ". It might not exist!"

    # Returns a user's card collection (the card name and the amount they own)
    def get_collection(self, command):
        return self.card_storage.get_collection(command.user.username)

    # Gives a card to another user
    def trade_card(self, command):
        try:
            parts = command.args.split(" ")
            if len(parts) < 2:
                return "CafeTCG: Invalid command format! Please enter /tradecard @user cardname"

            from_user = command.user.username
            to_user = parts[0]
            to_user = to_user.strip('@')
            card_name = command.args[command.args.index(" ") + 1:]
        except TypeError:
            return "CafeTCG: Invalid command format! Please enter command in the format: /tradecard @user cardname"
        except ValueError:
            return "CafeTCG: Invalid command format! Please enter /tradecard @user cardname"

        if not self.card_storage.account_exists(to_user):
            return "CafeTCG: {} is not a registered player! Please register using /tcgregister".format(to_user)

        if self.card_storage.remove_card(from_user, card_name):
            self.card_storage.add_card(to_user, card_name)
            return "CafeTCG: {} has given a {} to {}!".format(from_user, card_name, to_user)
        return "CafeTCG: Unable to send {} to {}. That card doesn't exist!".format(card_name, to_user)

    # Checks the honor balance of a user's account
    def check_balance(self, command):
        return self.account_manager.get_funds(command.user.username)

    # Sends honor to another user, subtracting that amount from the sender
    def make_payment(self, command):
        try:
            parts = command.args.split(" ")
            if not len(parts) == 2:
                return "CafeTCG: Invalid command format! Please enter /pay @user amount"

            from_user = command.user.username
            to_user = parts[0]
            to_user = to_user.strip('@')
            amount = int(parts[1])
        except TypeError:
            return "CafeTCG: Invalid command format! Please enter /pay @user amount"
        except ValueError:
            return "CafeTCG: Invalid command format! Please enter /pay @user amount"

        if amount <= 0:
            return "CafeTCG: Invalid amount of honor. Please enter something positive."
        if not self.card_storage.account_exists(to_user) or not self.account_manager.account_exists(to_user):
            return "CafeTCG: {} is not a registered player! Please register using /tcgregister".format(to_user)

        try:
            if self.account_manager.charge(from_user, amount):
                if self.account_manager.pay(to_user, amount):
                    self.account_manager.save_accounts()
                    return "CafeTCG: {} has paid {} honor to {}!".format(from_user, amount, to_user)
                return "CafeTCG: Invalid amount of honor. Please enter something positive."
        except TypeError:
            return "CafeTCG: Invalid command format! Please enter /pay @user amount"

    # Registers a user to use CafeTCG commands
    def register(self, command):
        if not self.card_storage.account_exists(command.user.username) and not\
                self.account_manager.account_exists(command.user.username):

            self.card_storage.create_account(command.user.username)
            print("CafeTCG: Created card account for " + command.user.username)
            self.account_manager.create_account(command.user.username)
            print("CafeTCG: Created honor account for " + command.user.username)
            return "CafeTCG: Account created for {}".format(command.user.username)
        return "CafeTCG: Unable to create account for {}. It already exists!".format(command.user.username)

    # Get completion status of an accounts collection
    def completion_status(self, command):
        if self.card_storage.account_exists(command.user.username):
            with open(self.dir + "/" + command.user.username + ".json", "r+") as f:
                data = json.load(f)
                total = len(data)
                values = data.values()
                count = 0

                for item in values:
                    if item >= 1:
                        count += 1

                f.seek(0)
                f.close()

                return "CafeTCG: {}'s collection is {}% complete!".format(command.user.username.strip(".json"),
                                                                 str(round((count / total) * 100, 3)))
        return "CafeTCG: {} is not a registered player! Please register using /tcgregister"\
            .format(command.user.username)

    # Returns a string with all available card packs
    def pack_list(self):
        return self.pack_manager.pack_list()

    # Shows a changelog of new features and changes
    def change_log(self):
        changes = "1. Added /selldups \n" +\
                  "2.  \n" +\
                  "3.  \n" + \
                  "4.  \n"
        return changes

    # Shows all cards that can be found in a collection
    def set_collection(self, command):
        if len(command.args) < 1 or command.args == "":
            return "CafeTCG: Invalid command format! Please enter /contents [pack-name]"
        elif self.pack_manager.pack_exists(command.args):
            return self.pack_manager.pack_collection(command.args)
        else:
            return "CafeTCG: Invalid pack name! Please enter /packs to see a list of available packs."

    def missing_cards(self, command):
        if self.card_storage.account_exists(command.user.username):
            with open(self.dir + "/" + command.user.username + ".json", "r+") as f:
                data = json.load(f)
                cards_needed = []

                for card in data.keys():
                    if data[card] == 0:
                        cards_needed.append(card)

                f.seek(0)
                f.close()

                response = "You still need the following cards to complete your collection: \n"

                for card in cards_needed:
                    response += card + "\n"

                return response

        return "CafeTCG: {} is not a registered player! Please register using /tcgregister" \
            .format(command.user.username)

    def award_honor(self, command):
        if command.user.username == "Klawk":
            try:
                parameter = command.args.split()
                name = parameter[0].strip('@')
                amount = int(parameter[1])

                if self.account_manager.account_exists(name):
                    if amount > 0:
                        self.account_manager.pay(name, amount)
                        self.account_manager.save_accounts()
                        return "CafeTCG: Payed {} {} honor!".format(name, amount)
                    return "CafeTCG: Please enter a positive amount!"
                return "CafeTCG: {} is not a registered player! Please register using /tcgregister"

            except TypeError:
                return "CafeTCG: Invalid command format! Please enter /award [name] [amount]"
            except ValueError:
                return "CafeTCG: Invalid command format! Please enter /award [name] [amount]"
        return "CafeTCG: Don't go messing around with admin commands you little hacker you!"

    def award_card(self, command):
        if command.user.username == "Klawk":
            try:
                parameter = command.args.split()
                name = parameter[0].strip('@')
                card_name = command.args[command.args.index(" ") + 1:]

                if self.account_manager.account_exists(name):
                    if not self.get_card(card_name) is None:
                        self.card_storage.add_card(name, card_name)
                        self.account_manager.save_accounts()
                        return "CafeTCG: Gave {} a {}!".format(name, card_name)
                    return "CafeTCG: {} is not a valid card! Please enter another!".format(card_name)
                return "CafeTCG: {} is not a registered player! Please register using /tcgregister".format(name)

            except TypeError:
                return "CafeTCG: Invalid command format! Please enter / [name] [card_name]"
            except ValueError:
                return "CafeTCG: Invalid command format! Please enter /award [name] [card_name]"
        return "CafeTCG: Don't go messing around with admin commands you little hacker you!"

    def sell_duplicates(self, command):
        if self.card_storage.account_exists(command.user.username):
            collection = self.card_storage.get_collection_list(command.user.username)

            total_cards = 0
            total_value = 0

            for key in collection.keys():
                if collection[key] > 1:
                    while collection[key] > 1:
                        collection[key] = collection[key] - 1
                        self.card_storage.remove_card(command.user.username, key.name)
                        value = self.get_card(key.name).honor
                        total_cards += 1
                        total_value += value
                        self.account_manager.pay(command.user.username, value)

            return "CafeTCG: You have sold {} card(s) for {} honor!".format(total_cards, total_value)

    def on_command(self, command):
        if command.command == "tcgregister":
            return {"type": "message", "message": self.register(command)}

        if not self.card_storage.account_exists(command.user.username) and not \
                self.account_manager.account_exists(command.user.username):
            return {"type": "message", "message": "{} is not a registered player!"
                                                  " Please register using /tcgregister".format(command.user.username)}
        else:
            if command.command == "booster":
                return {"type": "message", "message": self.open_pack(command)}
            elif command.command == "read":
                return {"type": "message", "message": self.read_card(command)}
            elif command.command == "sell":
                return {"type": "message", "message": self.sell_card(command)}
            elif command.command == "collection":
                return {"type": "message", "message": self.get_collection(command)}
            elif command.command == "trade":
                return {"type": "message", "message": self.trade_card(command)}
            elif command.command == "balance":
                return {"type": "message", "message": self.check_balance(command)}
            elif command.command == "pay":
                return {"type": "message", "message": self.make_payment(command)}
            elif command.command == "completion":
                return {"type": "message", "message": self.completion_status(command)}
            elif command.command == "packs":
                return {"type": "message", "message": self.pack_list()}
            elif command.command == "changelog":
                return {"type": "message", "message": self.change_log()}
            elif command.command == "contents":
                return {"type": "message", "message": self.set_collection(command)}
            elif command.command == "missing":
                return {"type": "message", "message": self.missing_cards(command)}
            elif command.command == "awardhonor":
                return {"type": "message", "message": self.award_honor(command)}
            elif command.command == "awardcard":
                return {"type": "message", "message": self.award_card(command)}
            elif command.command == "selldups":
                return {"type": "message", "message": self.sell_duplicates(command)}

    def get_commands(self):
        return {"booster", "read", "sell", "collection", "trade",
                "balance", "pay", "tcgregister", "completion", "packs",
                "changelog", "contents", "missing", "awardhonor", "awardcard",
                "selldups"}

    def get_name(self):
        return "Cafe TCG"

    def get_help(self):
        return "/booster [packname] \n /read [cardname] \n /sell [cardname] \n /collection \n " \
               "/trade [@user] [cardname] \n /balance \n /pay [@user] [amount] \n /tcgregister \n" \
               "/missing \n /selldups"


"""
Stores basic information on cards
"""


class Card:
    def __init__(self, card_info):
        self.card_type = card_info["type"]
        self.card_id = card_info["id"]
        self.card_set = card_info["set"]
        self.name = card_info["name"]
        self.honor = card_info["honor"]
        self.cred = card_info["cred"]
        self.desc = card_info["desc"]
        self.ability = card_info["ability"]
        self.faction = card_info["faction"]
        self.rarity = card_info["rarity"]

    def long_desc(self):
        long_desc = "Type: " + str(self.card_type) + "\n"
        long_desc += "ID: " + str(self.card_id) + "\n"
        long_desc += "Set: " + str(self.card_set) + "\n"
        long_desc += "Name: " + str(self.name) + "\n"
        long_desc += "Value: " + str(self.honor) + "\n"
        long_desc += "Credibility: " + str(self.cred) + "\n"
        long_desc += "Description:" + str(self.desc) + "\n"
        long_desc += "Ability: " + str(self.ability) + "\n"
        long_desc += "Faction: " + str(self.faction) + "\n"
        long_desc += "Rarity: " + str(self.rarity)
        return long_desc


"""
Stores sets of cards and their rarity.
Capable of randomly drawing cards for 'opening packs'
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
            if common.rarity == "Common":
                self.common_list.append(common)
        for uncommon in self.card_list:
            if uncommon.rarity == "Uncommon":
                self.uncommon_list.append(uncommon)
        for rare in self.card_list:
            if rare.rarity == "Rare":
                self.rare_list.append(rare)
        for ultra_rare in self.card_list:
            if ultra_rare.rarity == "Ultra-Rare":
                self.ultra_rare_list.append(ultra_rare)

    def draw_card(self, rarity_pack):
        rand = random.randint(0, len(rarity_pack) - 1)
        return rarity_pack[rand]

    def open_card_pack(self):
        card_pack = []
        for x in range(0, 3):
            rand = random.randint(1, 101)
            # 55% odds at common
            if 1 <= rand <= 55:
                card_pack.append(self.draw_card(self.common_list))
            # 30% odds at uncommon
            elif 56 <= rand <= 85:
                card_pack.append(self.draw_card(self.uncommon_list))
            # 13% odds at rare
            elif 86 <= rand <= 98:
                card_pack.append(self.draw_card(self.rare_list))
            # 2%
            else:
                card_pack.append(self.draw_card(self.ultra_rare_list))
        return card_pack

    def view_set_list(self):
        set_collection = ""

        for card in self.card_list:
            set_collection += card.name + "\n"
        return set_collection


class PackManager:
    def __init__(self, cardlist):
        self.cardlist = cardlist
        self.cardpacks = {}
        self.parse_packs(cardlist)

    # Dynamically creates card packs based on set names
    def parse_packs(self, cardlist):
        sets = []

        for card in cardlist:
            if not sets.__contains__(card.card_set):
                sets.append(card.card_set)

        for card_set in sets:
            card_set_list = []
            for card in cardlist:
                if card.card_set == card_set:
                    card_set_list.append(card)
            self.cardpacks[card_set] = CardPack(card_set_list)

    def open_pack(self, pack_name):
        return self.cardpacks[pack_name].open_card_pack()

    def pack_exists(self, pack_name):
        return self.cardpacks[pack_name]

    def pack_list(self):
        if self.cardpacks:
            desc = "The following packs may be bought: \n"
            for pack in self.cardpacks:
                desc += pack + " \n"
            return desc
        return "CafeTCG: No packs are available!"

    def pack_collection(self, pack_name):
        set_collection = "The following cards are found within the set " + pack_name + "\n"
        return set_collection + self.cardpacks[pack_name].view_set_list()


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
                data[item.name] = 0

            json.dump(data, f, sort_keys=True, indent=4)
            f.close()

    # Updates json data for user accounts when new card sets are added
    # IMPORTANT: IF A SET IS REMOVED ALL CARDS IN A USERS JSON DATA WILL BE REMOVED!
    def update_accounts(self):
        try:
            for file in os.listdir(self.dir):
                if file.endswith(".json") and not file == "honor.json":
                    with open(os.path.join(self.dir, file), "r+") as f:
                        old_data = json.load(f)
                        new_data = {}

                        for item in self.card_list:
                            if item.name in old_data:
                                new_data[item.name] = old_data[item.name]
                            else:
                                new_data[item.name] = 0

                        f.seek(0)
                        json.dump(new_data, f, sort_keys=True, indent=4)
                        f.truncate()
                        f.close()
        except NotADirectoryError:
            print("CafeTCG: Unable to open account card files!")

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
                if card.name == card_name:
                    value = data[card.name]
                    if value > 0:
                        value -= 1
                        data[card.name] = value
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
                value = data[card.name]

                if value > 0:
                    collection += card.name + " | " + str(value) + "\n"

            f.seek(0)
            f.close()
            return collection

    def get_collection_list(self, name):
        with open(self.dir + "/" + name + ".json", "r+") as f:
            data = json.load(f)

            collection = {}

            for card in self.card_list:
                value = data[card.name]

                if value > 0:
                    collection[card] = value

            f.seek(0)
            f.close()
            return collection


class Quest:
    def __init__(self, pack_manager, pack_list):
        self.pack_manager = pack_manager
        self.pack_list = pack_list
        self.cost = {} # Done
        self.reward = {} # Done
        self.quest_name = "" # TODO: Finish
        self.desc = "" # TODO: Finish
        self.quest_type = "" # Done
        self.completed = False

    def create_quest(self):
        rand_award = random.randint(0, 2)
        self.cost = {}
        self.reward = {}

        if rand_award == 0:  # Looks like the reward is honor!
            rand_honor = random.randint(50, 1801)
            self.reward["Honor"] = rand_honor
        elif rand_award == 1:  # Looks like the reward is a card!
            rand_pack = random.randint(0, len(self.pack_list))
            pack = self.pack_list[rand_pack]

            rand_rarity = random.randint(0, 4)

            quantity = 0
            card = Card

            if rand_rarity == 0:
                quantity = random.randint(1, 11)
                card = self.pack_manager.pack_exists(pack).draw_card("Common")
            elif rand_rarity == 1:
                quantity = random.randint(1, 9)
                card = self.pack_manager.pack_exists(pack).draw_card("Uncommon")
            elif rand_rarity == 2:
                quantity = random.randint(1,4)
                card = self.pack_manager.pack_exists(pack).draw_card("Rare")
            elif rand_rarity == 3:
                quantity = 1
                card = self.pack_manager.pack_exists(pack).draw_card("Ultra-Rare")
            self.reward["Card"] = card
            self.reward["Quantity"] = quantity

        if rand_award == 0: # Looks like quest requirement is a card to get honor!
            pack = random.randint(0, len(self.pack_list))
            self.quest_type = "Card"
            honor = self.reward["Quantity"]

            if 50 <= honor <= 300:
                quantity = random.randint(1, 11)
                card = self.pack_manager.pack_exists(pack).draw_card("Common")
            elif 301 <= honor <= 600:
                quantity = random.randint(1, 9)
                card = self.pack_manager.pack_exists(pack).draw_card("Uncommon")
            elif 601 <= honor <= 1001:
                quantity = random.randint(1, 4)
                card = self.pack_manager.pack_exists(pack).draw_card("Rare")
            else:
                quantity = random.randint(1, 2)
                card = self.pack_manager.pack_exists(pack).draw_card("Ultra-Rare")

            self.cost["Card"] = card
            self.cost["Quantity"] = quantity
        elif rand_award == 1: # Looks like quest requirement is honor to get some cards!
            self.quest_type = "Honor"
            quantity = 0
            rarity = self.reward["Card"].rarity

            if rarity == "Common":
                quantity = random.randint(25, 151)
            elif rarity == "Uncommon":
                quantity = random.randint(50, 351)
            elif rarity == "Rare":
                quantity = random.randint(100, 601)
            elif rarity == "Ultra-Rare":
                quantity = random.randint(200, 1201)
            self.cost["Honor"] = quantity

    def generate_name(self):
        rand_name = random.randint(0,51)

    def generate_lore(self):
        rand_lore = random.randint(0,101)

    def generate_quest_name(self):
        return None


class QuestManager:
    def __init__(self, directory, pack_manager):
        self.dir = directory
        self.pack_manager = pack_manager
        self.packs = []
        for pack in self.pack_manager.cardpacks:
            self.packs.append(pack)
        self.quests = []

    def make_quest(self):
        self.quests.append(Quest(self.pack_manager, self.packs))
        return "CafeTCG: A new quest has been created!"

    def check_quests(self):
        message = "CafeTCG: The following are completed quests: \n"
        for quest in self.quests:
            if quest.completed:
                message += quest.name + "\n"
        return message

    def available_quests(self):
        message = "CafeTCG: The following are available quests: \n"
        for quest in self.quests:
            message += quest.name + "\n"
        return message

    def quest_exists(self, quest_name):
        for quest in self.quests:
            if quest.name == quest_name:
                return True
        return False

    def read_quest(self, quest_name):
        if self.quest_exists(quest_name):
            for quest in self.quests:
                if quest.name == quest_name:
                    return quest.desc
        return "CafeTCG: Quest does not exist!"

    def turn_in(self, player, quest_name):
        return None