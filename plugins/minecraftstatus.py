from mcstatus import MinecraftServer

from plugin import Plugin


def load(data_dir, bot):
    return MinecraftStatus(data_dir, bot)


"""
Created by Matthew Klawitter 1/9/2019
Last Updated: 1/9/2019
Version: v1.0.0.0
"""


class MinecraftStatus(Plugin):
    def __init__(self, data_dir, bot):
        self.data_dir = data_dir
        self.bot = bot
        host = "mc.marks.kitchen"
        self.server = MinecraftServer.lookup(host)


    def get_status(self):
        status = self.server.status()
        return "There are currently {} players connected.".format(status.players.online)

    def get_ping(self):
        return "The server responded in {}ms".format(self.server.ping())

    def get_players(self):
        query = self.server.query()
        return "The following players are connected: {}".format(", ".join(query.players.names))

    def on_command(self, command):
        if command.command == "mcstatus":
            return {"type": "message", "message": self.get_status()}
        elif command.command == "mcping":
            return {"type": "message", "message": self.get_ping()}
        elif command.command == "mcplayers":
            return {"type": "message", "message": self.get_players()}

    def get_commands(self):
        return {"mcstatus", "mcping", "mcplayers"}

    def get_name(self):
        return "Minecraft Status"

    def get_help(self):
        return "'/mcstatus' to see how many players are currently connected\n \
                '/mcping' to see the server's ping\n \
                '/mcplayers' to see player names connected"