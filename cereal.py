import datetime
import json
import os
import urllib

from plugin import Plugin


def load(data_dir):
    return Cereal(data_dir)


"""
Created by Matthew Klawitter 9/18/2017
"""


class Cereal(Plugin):
    def __init__(self, data_dir):
        self.dir = data_dir
        self.cereal = {}

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        self.validate_date()
        self.build_cereals()

    def validate_date(self):
        date = datetime.date.today().strftime('%m/%d/%Y')

        if not os.path.isfile(self.dir + "/" + 'Date.txt'):
            with open(self.dir + "/" + 'Date.txt', 'w') as f:
                f.seek(0)
                f.write(date)
                f.close()
                return True
        elif self.is_empty(self.dir + "/" + 'Date.txt'):
            with open(self.dir + "/" + 'Date.txt', 'w') as f:
                f.seek(0)
                f.write(date)
                f.close()
                return True
        else:
            with open(self.dir + "/" + 'Date.txt', 'r') as f:
                if date.__eq__(f.read()):
                    f.close()
                    return True
                else:
                    f.close()
                    with open(self.dir + "/" + 'Date.txt', 'w') as f2:
                        f2.seek(0)
                        f2.write(date)
                        f2.close()
                        return False

    def build_cereals(self):
        response = urllib.request.urlopen(
            'https://raw.githubusercontent.com/MattKlawitter/Telegram-Response-Bot-KPlugins/master/cereal/cereals.json')

        cereal_data = json.loads(response.read().decode())
        total = len(cereal_data['cereals'])

        if total > 0:
            self.cereal['data'] = cereal_data
            self.cereal['total_count'] = total
        else:
            print("Uh oh... the json didn't load...")

        if not os.path.isfile(self.dir + "/" + 'CurrentCount.txt'):
            with open(self.dir + "/" + 'CurrentCount.txt', 'w') as f:
                f.seek(0)
                f.write("0")
                self.cereal['count'] = 0
                f.close()
        elif self.is_empty(self.dir + "/" + 'CurrentCount.txt'):
            with open(self.dir + "/" + 'CurrentCount.txt', 'w') as f:
                f.seek(0)
                f.write("0")
                self.cereal['count'] = 0
                f.close()
        else:
            with open(self.dir + "/" + 'CurrentCount.txt', 'r') as f:
                f.seek(0)
                self.cereal['count'] = int(f)
                f.close()

    def increment_count(self, increment):
        with open(self.dir + "/" + 'CurrentCount.txt', 'w') as f:
            if self.is_empty(self.dir + "/" + 'CurrentCount.txt'):
                f.seek(0)
                f.write("0")
                self.cereal['count'] = 0
                f.close()
            else:
                f.seek(0)
                f.write(str(self.cereal['count'] + increment))
                self.cereal['count'] = self.cereal['count'] + increment
                f.close()

    def reset_count(self):
        with open(self.dir + "/" + 'CurrentCount.txt', 'w') as f:
            f.seek(0)
            f.write("0")
            self.cereal['count'] = 0
            f.close()

    def is_empty(self, directory):
        return os.stat(directory).st_size == 0

    def get_cereal(self):
        if not self.validate_date():
            self.build_cereals()
            self.increment_count(1)

            if self.cereal['count'] < self.cereal['total_count']:
                cereal_of_the_day = self.cereal['data']['cereals'][self.cereal['count']]['Name']
                company = self.cereal['data']['cereals'][self.cereal['count']]['Url']
            else:
                self.reset_count()
                cereal_of_the_day = self.cereal['data']['cereals'][self.cereal['count']]['Name']
                company = self.cereal['data']['cereals'][self.cereal['count']]['Url']
        else:
            cereal_of_the_day = self.cereal['data']['cereals'][self.cereal['count']]['Name']
            company = self.cereal['data']['cereals'][self.cereal['count']]['Url']

        return " The cereal of the day is: " + str(cereal_of_the_day) + "! This tasty treat is made by " + company

    def on_command(self, command):
        if command.command == "cerealoftheday":
            return self.get_cereal()

    def get_commands(self):
        return {"cerealoftheday"}

    def get_name(self):
        return "Cereal of the Day"

    def get_help(self):
        return "/cerealoftheday"
