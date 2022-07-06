import inquirer
from inquirer import errors
from colorama import Fore
import json
from os.path import exists
import socket
from pynput import keyboard
import re
import requests
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("dev", nargs="?", help="Enable developer mode")
args = parser.parse_args()
multiplayer = False

if "dev" not in args or not args.dev == "true":
    print(f"{Fore.GREEN}Updating game index...")
    try:
        url = "https://raw.githubusercontent.com/djoamersfoort/lichtkrant-client/main/games.json"
        r = requests.get(url, allow_redirects=False)
        open('games.json', 'wb').write(r.content)
    except requests.exceptions.ConnectionError as e:
        print(f"{Fore.RED}No connection possible to github! Staying on old game index")
else:
    print(f"{Fore.YELLOW}Entering client in developer mode! Game index may not be up to date")

if exists("games.json"):
    with open("games.json") as f:
        games = json.load(f)
else:
    print(f"{Fore.RED}No game index found! Exiting")
    exit(1)

settings = {"ip": "100.64.0.65", "color": "#32a883", "multiplayer": False}
if exists("settings.json"):
    with open("settings.json") as f:
        settings = json.load(f)


class Page:
    name = None

    @staticmethod
    def cancel():
        exit(0)

    def options(self):
        return []

    @staticmethod
    def formatItem(item):
        if item["type"] == "toggle":
            if settings[item["var"]]:
                return f"{item['name']} [x]", item['name']
            else:
                return f"{item['name']} [ ]", item['name']

        return item['name']

    def open(self):
        options = self.options()

        answers = inquirer.prompt([
            inquirer.List(
                "option",
                message=self.name,
                choices=list(map(self.formatItem, options)),
            )
        ])
        if answers is None:
            return self.cancel()

        for option in options:
            if option["name"] == answers["option"]:
                if option["type"] == "input":
                    value = inquirer.prompt([
                        inquirer.Text(
                            "value",
                            message=option["name"],
                            validate=option["validate"]
                        )
                    ])

                    settings[option["storage"]] = value["value"]
                    with open("settings.json", "w") as fw:
                        json.dump(settings, fw)

                    print(f"{Fore.GREEN}{option['name']} set to {value['value']}")
                    self.open()
                elif option["type"] == "page":
                    option["page"].open()
                elif option["type"] == "game":
                    print(f"{Fore.GREEN}Now playing {option['name']}!")
                    Game(option["game"])
                elif option["type"] == "toggle":
                    if settings[option["var"]]:
                        settings[option["var"]] = False
                    else:
                        settings[option["var"]] = True
                    self.open()


class MainPage(Page):
    name = "Choose a game"

    @staticmethod
    def format(game):
        return {
            "name": game["name"],
            "type": "game",
            "game": game
        }

    def options(self):
        return \
            [
                {
                    "name": "Local multiplayer",
                    "type": "toggle",
                    "var": "multiplayer"
                }
            ] + list(map(self.format, games)) + [
                {
                    "name": "Settings",
                    "type": "page",
                    "page": SettingsPage()
                }
            ]


class SettingsPage(Page):
    name = "Settings"

    @staticmethod
    def cancel():
        MainPage().open()

    @staticmethod
    def isHex(answers, string):
        if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', string):
            print(f"{Fore.RED}Color must be a valid HEX Code")
            raise errors.ValidationError('', reason=f"{Fore.RED}Color must be a valid HEX Code")
        return True

    def options(self):
        return [
            {
                "name": "Preferred color",
                "type": "input",
                "storage": "color",
                "validate": self.isHex
            },
            {
                "name": "IP",
                "type": "input",
                "storage": "ip",
                "validate": True
            },
            {
                "name": "Go back",
                "type": "page",
                "page": MainPage()
            }
        ]


class Game:
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, game):
        try:
            self.socket.connect((settings["ip"], game["port"]))
        except socket.error as e:
            print(f"{Fore.RED}Something went wrong while making a connection to {settings['ip']}:{game['port']}!")
            print(f"{Fore.WHITE}{e}")
            exit(1)

        self.game = game

        self.keys = {}
        for key in game["keys"]:
            self.keys[key] = False
        self.send()

        if game["colors"]["configurable"]:
            self.socket.sendall(settings["color"].encode())

        while True:
            with keyboard.Listener(on_release=self.release, on_press=self.press) as l:
                l.join()

    def release(self, key):
        if hasattr(key, "char") and key.char in self.keys:
            self.keys[key.char] = False
            self.send()

    def press(self, key):
        if hasattr(key, "char") and key.char in self.keys:
            self.keys[key.char] = True
            self.send()

    def msg(self):
        string = "".join([
            f"{int(value)}" for key, value in self.keys.items()
        ])
        if self.game["colors"]["configurable"]:
            while len(string) < 7:
                string += " "

        return string.encode()

    def send(self):
        self.socket.sendall(self.msg())


try:
    MainPage().open()
except KeyboardInterrupt:
    exit(0)
