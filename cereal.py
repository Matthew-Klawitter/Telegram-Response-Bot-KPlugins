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
        self.data_failure = "Failed to load cereal data set!"

        if not os.path.exists(self.dir):
            os.makedirs(self.dir)

        self.build_cereals()
        self.validate_date()

    def build_cereals(self):
        response = urllib.request.urlopen(
            'https://raw.githubusercontent.com/MattKlawitter/Telegram-Response-Bot-KPlugins/master/cereal/cereals.json')
        cereal_data = json.loads(response.read().decode())
        total = len(cereal_data['cereals'])

        if total is None or total > 0:
            self.cereal['data'] = cereal_data
            self.cereal['total_count'] = total
            self.cereal["failure"] = False
        else:
            print("Uh oh, could not load json! This might be rip!")
            self.cereal["failure"] = True

        if not self.file_exists(self.dir + "/" + 'CurrentCount.txt'):
            with open(self.dir + "/" + 'CurrentCount.txt', 'w') as f:
                f.seek(0)
                f.write("0")
                self.cereal['count'] = 0
                f.close()
        else:
            with open(self.dir + "/" + 'CurrentCount.txt', 'r') as f:
                f.seek(0)
                self.cereal['count'] = int(f.read())
                f.close()

    def validate_date(self):
        date = datetime.date.today().strftime('%m/%d/%Y')

        if not self.file_exists(self.dir + "/" + 'Date.txt'):
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
                    self.increment_count(1)
                    with open(self.dir + "/" + 'Date.txt', 'w') as f2:
                        f2.seek(0)
                        f2.write(date)
                        f2.close()
                        return False

    def increment_count(self, increment):
        with open(self.dir + "/" + 'CurrentCount.txt', 'w') as f:
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

    def file_exists(self, directory):
        return os.path.isfile(directory) and os.path.getsize(directory) > 0

    def get_cereal(self):
        if not self.validate_date():
            self.build_cereals()

            if self.cereal["failure"]:
                return self.data_failure
            elif self.cereal['count'] < self.cereal['total_count']:
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
