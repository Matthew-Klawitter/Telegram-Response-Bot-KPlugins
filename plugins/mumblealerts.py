import datetime
import socket
import threading
from struct import pack, unpack

from plugin import Plugin
from time import sleep



"""
Created by Matthew Klawitter 11/13/2018
Last Updated: 9/18/2019
Version: v2.1.0.0
Credit to https://gist.github.com/azlux for mumble ping algorithm https://gist.github.com/azlux/315c924af4800ffbc2c91db3ab8a59bc
"""



class BotPlugin(Plugin):
    def __init__(self, data_dir, bot):
        self.data_dir = data_dir
        self.bot = bot
        self.channels = []
        self.current_users = self.connected_users()

        thread = threading.Thread(target = self.return_status)
        thread.daemon = True
        thread.start()

    def connected_users(self, host="localhost", port=64738):
        """ 
            <host> [<port>]
            Ping the server and display results.
        """

        try:
            addrinfo = socket.getaddrinfo(host, port, 0, 0, socket.SOL_UDP)
        except socket.gaierror as e:
            print(e)
            return

        for (family, socktype, proto, canonname, sockaddr) in addrinfo:
            s = socket.socket(family, socktype, proto=proto)
            s.settimeout(2)

            buf = pack(">iQ", 0, datetime.datetime.now().microsecond)
            try:
                s.sendto(buf, sockaddr)
            except (socket.gaierror, socket.timeout) as e:
                continue

            try:
                data, addr = s.recvfrom(1024)
            except socket.timeout:
                continue

            r = unpack(">bbbbQiii", data)

            # version = r[1:4]
            # https://wiki.mumble.info/wiki/Protocol
            # r[0,1,2,3] = version
            # r[4] = ts (indent value)
            # r[5] = users
            # r[6] = max users
            # r[7] = bandwidth

            return r[5]

    def return_status(self):
        while threading.main_thread().is_alive():
            updated_users = self.connected_users()

            if updated_users != self.current_users:
                if len(self.channels) > 0:
                    message = ""

                    if self.current_users < updated_users:
                        message = "A user has joined the mumble server. There are now " + str(updated_users) + " connected."
                        self.current_users = updated_users
                    elif self.current_users > updated_users:
                        message = "A user has left the mumble server. There are now " + str(updated_users) + " connected."
                        self.current_users = updated_users

                    for channel in self.channels:
                        self.bot.send_message(channel, message)
                else:
                    self.current_users = updated_users
            sleep(15)

    def com_enable(self, command):
        for channel in self.channels:
            if channel == command.chat.id:
                return {"type": "message", "message": "This channel is already authorized for mumble alerts."}
        self.channels.append(command.chat.id)
        return {"type": "message", "message": "Enabled mumble alerts for this channel."}

    def com_disable(self, command):
        for channel in self.channels:
            if channel == command.chat.id:
                self.channels.remove(channel)
                return {"type": "message", "message": "Disabled mumble alerts for this channel."}
        return {"type": "message", "message": "Alerts have not been enabled for this channel."}

    def com_add(self, command):
        channel = command.args
        
        if channel in self.channels:
            return {"type": "message", "message": "This channel is already authorized for mumble alerts."}
        self.channels.append(command.chat.id)
        return {"type": "message", "message": "Enabled mumble alerts for this channel."}

    def com_rm(self, command):
        channel = command.args

        if channel in self.channels:
            self.channels.remove(channel)
            return {"type": "message", "message": "Disabled mumble alerts for this channel."}
        return {"type": "message", "message": "Alerts have not been enabled for this channel."}

    def on_command(self, command):
        if command.command == "menable":
            return self.com_enable(command)    
        elif command.command == "mdisable":
            return self.com_disable(command)
        elif command.command == "madd":
            return self.com_add(command)
        elif command.command == "mrm":
            return self.com_rm(command)

    def get_commands(self):
        return {"menable", "mdisable", "madd", "mrm"}

    def get_name(self):
        return "Mumble Alerts"

    def get_help(self):
        return "Mumble Alerts Help Doc\n" \
               "'menable' to enable alerts in the current channel\n" \
               "'mdisable' to disable alerts in the current channel\n" \
               "'madd [channel]' to enable alerts in a specified channel\n" \
               "'mrm [channel]' to disable alerts in a specified channel\n"

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