import json
import os
import urllib

from plugin import Plugin


def load(data_dir):
    return CafeTCG(data_dir)


"""
Created by Matthew Klawitter 11/15/2017
"""


class CafeTCG(Plugin):
    def __init__(self, data_dir):
        self.dir = data_dir
        self.cafetcg = {}
        self.cardlist = []
        self.data_failure = "Failed to load tcg data set!"

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        self.build_cards()

    def build_cards(self):
        response = urllib.request.urlopen(
            'https://raw.githubusercontent.com/MattKlawitter/Telegram-Response-Bot-KPlugins/dev/Cafe_TCG/Cafe_TCG.json')
        card_data = json.loads(response.read().decode())
        total = len(card_data['Character'])

        if total is not None or total > 0:
            self.cafetcg['total_count'] = total
            self.cafetcg["failure"] = False
        else:
            print("Uh oh, could not load json! This might be rip!")
            self.cafetcg["failure"] = True

        with open(self.dir + "/" + "cardbackup.txt", "w+") as f:
            f.seek(0)
            f.write("Backup here eventually..." + "There are " + str(total) + " cards!")
            f.close()

        if not self.cafetcg["failure"]:
            self.parse_cardlist(card_data["Character"], "Character")
            self.parse_cardlist(card_data["Ability"], "Ability")
            self.parse_cardlist(card_data["Item"], "Item")
            self.parse_cardlist(card_data["Location"], "Location")
            self.parse_cardlist(card_data["Argument"], "Argument")

        else:
            print(self.data_failure)
            print("Using backup data... NYI!!!")

    def parse_cardlist(self, datalist, type):
        for item in datalist:
            card_info = {}

            card_info["type"] = type
            card_info["name"] = item["Info"]["Title"]
            card_info["id"] = item["Info"]["ID"]
            card_info["honor"] = item["Info"]["Honor"]
            card_info["cred"] = item["Info"]["Credibility"]
            card_info["desc"] = item["Info"]["Description"]
            card_info["ability"] = item["Info"]["Ability"]
            card_info["faction"] = item["Info"]["Faction"]
            card_info["rarity"] = item["Info"]["Rarity"]

            card = Card(card_info)
            self.cardlist.append(card)

    def open_pack(self):
        return str(self.cardlist[0].long_desc())

    def read_card(self, command):
        return self.cardlist[0].get_name()

    def sell_card(self, command):
        return self.cardlist[0].get_name()

    def get_collection(self, user):
        return self.cardlist[0].get_name()

    def file_exists(self, directory):
        return os.path.isfile(directory) and os.path.getsize(directory) > 0

    def on_command(self, command):
        if command.command == "openpack":
            return self.open_pack()
        elif command.command == "readcard":
            return self.read_card(command)
        elif command.command == "sellcard":
            return self.sell_card(command)
        elif command.command == "mycollection":
            return self.get_collection(command.user)

    def get_commands(self):
        return {"openpack", "readcard", "sellcard", "mycollection"}

    def get_name(self):
        return "Cafe TCG"

    def get_help(self):
        return "/cafetcg"

class Card():
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
