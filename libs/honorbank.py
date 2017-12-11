import json
import os

from plugin import Plugin


def load(data_dir, bot):
    return HonorBank(data_dir, bot)


"""
Created by Matthew Klawitter 12/11/2017
Last Updated: 12/11/2017
Version: v1.0.2.2
"""


class HonorBank:
    def __init__(self):
        self.dir = "honor.json" # NYI
        self.currency_name = "honor"
        self.honor_accounts = {}
        self.load_accounts()

    def create_account(self, name):
        if not self.account_exists(name):
            self.honor_accounts[name] = 0
            self.save_accounts()
            return True
        return False

    def account_exists(self, name):
        if name in self.honor_accounts:
            return True
        return False

    def remove_account(self, name):
        del self.honor_accounts[name]

    def save_accounts(self):
        try:
            with open(self.dir, "w+") as f:
                json.dump(self.honor_accounts, f, sort_keys=True, indent=4)
                f.seek(0)
                f.close()
        except FileNotFoundError:
            print("HonorBank: Unable to find {}, creating a new file.").format(self.dir)

            # Ensure that the account file is created.
            file = open(self.dir, "r+")
            file.seek(0)
            file.close()

            self.save_accounts()

    def load_accounts(self):
        try:
            with open(self.dir, "r+") as f:
                self.honor_accounts = json.load(f)
                f.seek(0)
                f.close()
            print("HonorBank: Accounts successfully loaded!")
            return True
        except FileNotFoundError:
            print("HonorBank: Accounts failed to load!")
            return False
        except ValueError:
            print("HonorBank: Cannot load an empty file!")
            return False

    def get_funds(self, name):
        return self.honor_accounts[name]

    def pay(self, name, amount):
        if amount > 0:
            self.honor_accounts[name] += amount
            return True
        return False

    def charge(self, name, amount):
        if self.honor_accounts[name] >= amount:
            self.honor_accounts[name] -= amount
            return True
        return False