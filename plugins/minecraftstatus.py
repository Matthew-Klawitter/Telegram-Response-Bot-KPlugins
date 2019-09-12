from mcstatus import MinecraftServer

from plugin import Plugin


def load(data_dir, bot):
    return MinecraftStatus(data_dir, bot)


"""
Created by Matthew Klawitter 1/9/2019
Last Updated: 3/3/2019
Version: v1.1.1.0
"""


class MinecraftStatus(Plugin):
    def __init__(self, data_dir, bot):
        self.data_dir = data_dir
        self.bot = bot
        self.is_setup = False
        self.server = None

    def setup(self, command):
        commands = command.args.split(" ")
        host = commands[0]
        self.server = MinecraftServer.lookup(host)
        self.is_setup = True
        return "MCStatus: Now pinging {} globally. Use /mcstatus /mcping /mcplayers to receive more information on this server.".format(host)

    def get_status(self):
        status = self.server.status()
        return "MCStatus: There are currently {} players connected.".format(status.players.online)

    def get_ping(self):
        return "MCStatus: The server responded in {}ms".format(self.server.ping())

    def get_players(self):
        status = self.server.status()
        response = "MCStatus: The following players are connected:\n"

        for player in status.players.sample:
            response += player.name + "\n"
        return response

    def on_command(self, command):
        if command.command == "mcsetup":
            return {"type": "message", "message": self.setup(command)}

        if not self.is_setup:
            return {"type": "message", "message": "MCStatus: Please first run /mcsetup [ip] to configure a server."}
        elif command.command == "mcstatus":
            return {"type": "message", "message": self.get_status()}
        elif command.command == "mcping":
            return {"type": "message", "message": self.get_ping()}
        elif command.command == "mcplayers":
            return {"type": "message", "message": self.get_players()}

    def get_commands(self):
        return {"mcsetup", "mcstatus", "mcping", "mcplayers"}

    def get_name(self):
        return "Minecraft Status"

    def get_help(self):
        return "'/mcstatus' to see how many players are currently connected\n \
                '/mcping' to see the server's ping\n \
                '/mcplayers' to see player names connected\n \
                '/mcsetup [ip]' to configure which server to obtain information on."
    
    def on_message(self, message):
        # Implement this if has_message_access returns True
        # message is some string sent in Telegram
        # return a response to the message
        return ""

    def has_message_access(self):
        return False
	
    def enable(self):
        pass

    def disable(self):
        pass