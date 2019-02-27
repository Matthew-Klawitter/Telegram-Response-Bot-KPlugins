import threading

from datetime import datetime
from plugin import Plugin
from time import sleep


# Called when the bot loads the plugin
# Instantiates this plugin and passes it the bot and plugin directory
def load(data_dir, bot):
    return HydrationAlerts(data_dir, bot)


"""
Created by Matthew Klawitter 12/5/2018
Last Updated: 12/5/2018
Version: v0.0.0.0
"""


# Main class of the plugin that handles all commands and interactions
class HydrationAlerts(Plugin):
    def __init__(self, data_dir, bot):
        # The directory in which this plugin can store data '/catchemall'
        self.dir = data_dir
        # A reference to the bot itself for more advanced operations
        self.bot = bot
        # A set containing all channels in which to send alerts to
        self.channels = set()
        # Bool that determines if it is daytime, which is the period during which messages may be sent
        self.is_day = True
        # Float amount of water to drink per hour in cups
        self.cup_quantity = .57
        # Float amount of water to drink per hour in liters
        self.liter_quantity = .14

        # Launches a deamon thread that handles alerts and random encounters
        thread = threading.Thread(target = self.hydration_alert)
        thread.daemon = True
        thread.start()

    def hydration_alert(self):
        while threading.main_thread().is_alive():
            time = datetime.now().time()
            hour = time.hour
            minutes = time.minute

            if hour == 0:
                self.message_channels("Wow it is late! If anyone is still up at this hour remember to stay hydrated! Drink at least .5C (.11L) of water per hour you stay awake!")
                self.is_day = False
            elif hour == 8:
                self.message_channels("It's the start of a new day and it's time to get hydrated!\nWithin the hour you should drink at least .5C (.11L) of water.")
                self.is_day = True
            else:
                if self.is_day:
                    elapsed_hours = hour - 8
                    current_hour = hour
                    current_cups = self.cup_quantity * elapsed_hours
                    current_liters = self.liter_quantity * elapsed_hours

                    if hour > 12:
                        current_hour -= 12

                    self.message_channels("It is now {} o'Clock! By this point in the day you should have drank {}C ({}L) of water to maintain optimal hydration!".format(current_hour, round(current_cups, 2), round(current_liters, 2)))

            sleep(60*(60 - minutes))

    # Helper method that messages all channels within self.channels
    def message_channels(self, message):
        for channel in self.channels:
            self.bot.send_message(channel, message)

    # Run whenever someone on telegram types one of these commands
    def on_command(self, command):
        if command.command == "hydration":
            if command.chat.id in self.channels:
                return {"type": "message", "message": "I'm already reminding you to stay hydrated!"}
            else:
                self.channels.add(command.chat.id)
                return {"type": "message", "message": "Ok! I will remind you to stay hydrated!"}
        elif command.command == "dehydration":
            if command.chat.id in self.channels:
                self.channels.remove(command.chat.id)
                return {"type": "message", "message": "I will no longer remind you to stay hydrated."}
            else:
                return {"type": "message", "message": "I am not currently set to remind you to stay hydrated."}

    # Commands that are enabled on the server. These are what triggers actions on this plugin
    def get_commands(self):
        return {"hydration", "dehydration"}

    # Returns the name of the plugin
    def get_name(self):
        return "HydrationAlerts"

    # Run whenever someone types /help cafesim
    def get_help(self):
        return "'/hydration' to enable alerts in this channel \n,\
                '/dehydration' to disable alerts in this channel\n"


