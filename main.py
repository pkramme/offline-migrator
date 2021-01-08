import argparse
import json
import pathlib
import uuid
from dataclasses import dataclass
from typing import List
import time

import requests


@dataclass
class Player:
    name: str
    offline_uuid: str
    online_uuid: str


def get_online_uuids(players: List[Player]) -> List[Player]:
    lenplayers = len(players)
    for i, player in enumerate(players):
        r = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{ player.name }?at={ int(time.time()) }")
        if not r.ok:
            print("Error contacting Mojang API, aborting")
            print(r.text)
            exit()

        print(f"({ i + 1}/{ lenplayers }) Checking online UUID for { player.name }...")
        if r.text != "":
            mojang_response = r.json()
            player.online_uuid = uuid.UUID(mojang_response["id"])
            players[i] = player
        else:
            print(f"Found no matching online UUID for { player.name }, the player probably renamed themselves.")

    return players


def load_players(user_cache_path: pathlib.Path) -> List[Player]:
    players: List[Player] = []
    user_cache_json = json.loads(user_cache_path.read_text())
    for user in user_cache_json:
        players.append(Player(user["name"], user["uuid"], ""))

    return players

def remove_uuidless_players(players: List[Player]) -> List[Player]:
    for i, player in enumerate(players):
        if player.online_uuid == "":
            del players[i]
    return players


def rename_playerdata(playerdata_path: pathlib.Path, players: List[Player]):
    for player in players:
        old_player_dat = playerdata_path.joinpath(pathlib.Path(player.offline_uuid)).with_suffix(".dat")
        new_player_dat = playerdata_path.joinpath(pathlib.Path(player.online_uuid)).with_suffix(".dat")
        if old_player_dat.exists() and not new_player_dat.exists():
            old_player_dat.rename(new_player_dat)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--dryrun", type=bool)
    argparser.add_argument("playerdata", type=str)
    argparser.add_argument("usercache", type=str)
    args = argparser.parse_args()

    user_cache_path = pathlib.Path(args.usercache).absolute()
    playerdata_path = pathlib.Path(args.playerdata).absolute()

    print("Loading players from", user_cache_path)
    players = load_players(pathlib.Path(args.usercache))

    print("Loading online UUIDs from Mojang")
    players = get_online_uuids(players)

    print("Removing players without UUID")
    players = remove_uuidless_players(players)

    for player in players:
        print(player.name, ":", player.offline_uuid, " -> ", player.online_uuid)

    if args.dryrun:
        print("Performing dry run, not changing anything")
    else:
        if input("Please confirm the changes above (y/N):") == "y":
            rename_playerdata(playerdata_path, players)
        else:
            print("Aborting!")
            exit()

    print("Done.")







if __name__ == '__main__':
    main()
