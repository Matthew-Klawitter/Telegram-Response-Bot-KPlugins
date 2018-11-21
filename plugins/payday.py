import os
import threading
from time import sleep
from threading import Timer
from libs.honorbank import HonorBank

from plugin import Plugin


def load(data_dir, bot):
    return Payday(data_dir, bot)


"""
Created by Matthew Klawitter 2/1/2018
Last Updated: 2/1/2018
Version: v1.0.0.1
"""


class Payday(Plugin):
    def __init__(self, data_dir, bot):
        self.account_manager = HonorBank()
        self.honor_accounts = self.account_manager.honor_accounts
        thread = threading.Thread(target = self.pay_day)
        thread.daemon = True
        thread.start()

    def pay_day(self):
        while threading.main_thread().is_alive():
            if self.honor_accounts:
                for account in self.honor_accounts.keys():
                    self.account_manager.pay(account, 50)
                    self.account_manager.save_accounts()
            sleep(3600)
