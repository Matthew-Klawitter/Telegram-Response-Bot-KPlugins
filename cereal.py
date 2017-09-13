import datetime
import json
import os
import urllib
from calendar import Calendar

import requests

from plugin import Plugin


def load(data_dir):
    return Cereal(data_dir)


class Cereal(Plugin):
    def __init__(self, data_dir):
        self.dir = data_dir
        self.cereal = {}
        date = datetime.date.today()
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        with open(self.dir + "/" + 'date.txt', 'w') as f:
            if f.mode == 'r':
                if not f.read().__eq__(date):
                    f.write(date)
        response = urllib.request.urlopen(
            'https://raw.githubusercontent.com/MattKlawitter/Telegram-Response-Bot-KPlugins/master/cereal/cereals.json')
        cereal_data = json.loads(response.read().decode())
        count = len(cereal_data['cereals'])
        print(cereal_data['cereals'][0]["Name"])

    def get_cereal(self):
        return self.cereal

    def on_command(self, command):
        if command.command == "cerealoftheday":
            return self.get_word()

    def get_commands(self):
        return {"cerealoftheday"}

    def get_name(self):
        return "Cereal of the Day"

    def get_help(self):
        return "/cerealoftheday"


class CerealCombo:
    def __init__(self, cereal, link, date):
        self.cereal = cereal
        self.link = link
        self.date = date
