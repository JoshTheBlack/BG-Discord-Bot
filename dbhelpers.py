
from tinydb import TinyDB, Query
from datetime import datetime

User = Query()
db = TinyDB('cfg/db.json')

def player_stats(playername, table, game="all"):
    player = table.get(User.name == playername)
    if player == None:
        return f'**{playername}** has **no** recorded game sessions.'
    games = "\n"
    if game == "all":
        for i in player["played"]:
            games += f'**{player["name"]}** has won **{player["played"][i]["wins"]}** of **{player["played"][i]["plays"]}** games (or {round(player["played"][i]["wins"]/player["played"][i]["plays"] * 100,0)}%) of **{i}**\n'
    else:
        for i in game:
            try:
                games += f'**{player["name"]}** has won **{player["played"][i]["wins"]}** of **{player["played"][i]["plays"]}** games (or {round(player["played"][i]["wins"]/player["played"][i]["plays"] * 100,0)}%) of **{i}**\n'
            except:
                games += f'**{player["name"]}** has not recorded any plays of {i}\n'
    return f"""**{player["name"]}** has won **{player["wins"]}** of all **{player["plays"]}** ({round(player["wins"]/player["plays"] * 100, 0)}%) games played.{games}\n"""

def init_config(config, location = "online", players = []):
    config.upsert({"id": "config", "version": "1", "location": location, "active" : players}, User.id == "config")
    return

def init_player(player, table):
    table.upsert({"name": player, "wins":0,"plays":0,"played": {}, "attendance": []}, User.name == player)
    return

def update_db(table, config, currentDBVersion):
    base = table.all()
    try:
        dbversion = int(config.get(User.id == "config")["version"])
    except:
        dbversion = 0
    while dbversion < currentDBVersion:
        if dbversion == 0:
            from tinydb.operations import delete
            for player in base:
                try:
                    table.update(delete('active'), User.name == player["name"])
                except:
                    pass
            init_config()
            dbversion += 1
    return f"db updated to version {dbversion}"

def get_db(ctx):
    table = db.table(ctx.guild.name)
    config = db.table(ctx.guild.name + ".config")
    return table, config
            
def set_players(ctx, players):
    table, config = get_db(ctx)
    for player in players:
        if not table.contains(User.name == player):
            init_player(player, table)
    conf = config.get(User.id == "config")
    if conf == None:
        init_config()
        conf = config.get(User.id == "config")
    conf["active"] = players
    config.upsert(conf, User.id == "config")

def get_active_players(ctx):
    _, config = get_db(ctx)
    return config.get(User.id == "config")["active"]

def record_play(game, winner, ctx):
    table, config = get_db(ctx)
    activePlayers = config.get(User.id == "config")["active"]
    set_players(ctx, activePlayers)
    players = table.all()
    location = config.get(User.id == "config")["location"]
    for player in players:
        if player["name"] in activePlayers:
            player["plays"] += 1
            date = datetime.today().strftime('%Y-%m-%d')
            if not any(date in list for list in player["attendance"]):
                player["attendance"].append([date,location])
            if game not in player["played"]:
                player["played"][game] = {"wins" : 0, "plays" : 0}
            player["played"][game]["plays"] += 1
            if player["name"] in winner:
                player["wins"] += 1
                player["played"][game]["wins"] += 1
            table.upsert(player,User.name == player["name"])

def get_attendance(playername, table):
    player = table.get(User.name == playername)
    if player == None:
        return f'**{playername}** has **no** recorded game sessions.'
    return f'**{playername}** has attended **{len(player["attendance"])}** recorded game session{"s" if len(player["attendance"]) != 1 else ""}.\n{player["attendance"]}'

def set_location(location, config):
    try:
        conf = config.get(User.id == "config")
        conf["location"] = location
        config.upsert(conf, User.id == "config")
    except:
        init_config(location)
    return f"Location set to {location}'s"

def get_location(config):
    try:
        location = config.get(User.id == "config")["location"]
    except:
        location = None
    return location

def del_players(players, table):
    message = ""
    for player in players:
        try:
            table.remove(User.name == player)
            message += f'{player} removed from database.\n'
        except:
            message += f'Something went wrong deleting {player}'
    return message

def del_games(games, table):
    base = table.all()
    for player in base:
        plays, wins = 0, 0
        for game in games:
            try:
                stats = player["played"].pop(game)
            except:
                continue
            player["plays"] -= stats["plays"]
            player["wins"] -= stats["wins"]
        table.update(player, User.name == player["name"])
    return "Done"

def recalculate(table):
    base = table.all()
    for player in base:
        player["wins"] = 0
        player["plays"] = 0
        for game in player["played"]:
            player["wins"] += player["played"][game]["wins"]
            player["plays"] += player["played"][game]["plays"]
        table.update(player, User.name == player["name"])
    return "Play and win counts have been recalculated for all players."
