import discord
import os
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from datetime import datetime

load_dotenv("cfg/.env")
db = TinyDB('cfg/db.json')
User = Query()
client = discord.Client()
currentDBVersion = 1

# db Format { "index" : { "name" : name, "wins": win counter, "plays": play counter, "played": {"game1" : {wins, plays}, "game2": {wins, plays}...}, attendance = [[date, location]...] }}
# conf db Format {"index" : {"id" : "config", "version": dbversion, "location": location, "players": [player1, ...]}}

@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))

@client.event
async def on_message(message, currentDBVersion=currentDBVersion, db=db, User=User):
    table = db.table(message.guild.name)
    config = db.table(message.guild.name + ".config")

    def init_config(location = "online", players = []):
        config.upsert({"id": "config", "version": "1", "location": location, "active" : players}, User.id == "config")
        return

    def init_player(player):
        table.upsert({"name": player, "wins":0,"plays":0,"played": {}, "attendance": []}, User.name == player)
        return

    def updatedb():
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
                
    def set_players(players):
        for player in players:
            if not table.contains(User.name == player):
               init_player(player)
        conf = config.get(User.id == "config")
        if conf == None:
            init_config()
            conf = config.get(User.id == "config")
        conf["active"] = players
        config.upsert(conf, User.id == "config")

    def get_active_players():
        return config.get(User.id == "config")["active"]

    def record_play(game, winner):
        activePlayers = config.get(User.id == "config")["active"]
        set_players(activePlayers)
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

    def player_stats(playername, game="all"):
        player = table.get(User.name == playername)
        if player == None:
            return f'**{playername}** has **no** recorded game sessions.'
        games = "\n"
        if game == "all":
            for i in player["played"]:
                games += f'**{player["name"]}** has won **{player["played"][i]["wins"]}** of **{player["played"][i]["plays"]}** games of **{i}**\n'
        else:
            for i in game:
                try:
                    games += f'**{player["name"]}** has won **{player["played"][i]["wins"]}** of **{player["played"][i]["plays"]}** games of **{i}**\n'
                except:
                    games += f'**{player["name"]}** has not recorded any plays of {i}\n'
        return f"""**{player["name"]}** has won **{player["wins"]}** of all **{player["plays"]}** games played.{games}\n"""

    def get_attendance(playername):
        player = table.get(User.name == playername)
        if player == None:
            return f'**{playername}** has **no** recorded game sessions.'
        return f'**{playername}** has attended **{len(player["attendance"])}** recorded game session{"s" if len(player["attendance"]) != 1 else ""}.\n{player["attendance"]}'

    def set_location(location):
        try:
            conf = config.get(User.id == "config")
            conf["location"] = location
            config.upsert(conf, User.id == "config")
        except:
            init_config(location)
        return f"Location set to {location}'s"

    def get_location():
        try:
            location = config.get(User.id == "config")["location"]
        except:
            location = None
        return location

    def del_players(players):
        message = ""
        for player in players:
            try:
                table.remove(User.name == player)
                message += f'{player} removed from database.\n'
            except:
                message += f'Something went wrong deleting {player}'
        return message

    def del_games(games):
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

    def recalc():
        base = table.all()
        for player in base:
            player["wins"] = 0
            player["plays"] = 0
            for game in player["played"]:
                player["wins"] += player["played"][game]["wins"]
                player["plays"] += player["played"][game]["plays"]
            table.update(player, User.name == player["name"])
        return "Play and win counts have been recalculated for all players."

    if message.author == client.user:
        return
    
    if message.content.startswith('!hi'):
        user = str(message.author)
        await message.channel.send(f'Hello! {user.split("#",1)[0]}')
    
    if message.content.startswith('!players'):
        players = str(message.content).split(' ',1)[1].replace(' ','').lower().split(',')
        set_players(players)
        await message.channel.send(f'Players set to {*players,}')
        
    if message.content.startswith('!record'):
        winner = str(message.content).split(' ',2)[1].lower().split(',')
        game = str(message.content).split(' ',2)[2].lower()
        record_play(game,winner)
        currentplayers = get_active_players()
        await message.channel.send(f'Recorded {winner} as the winner{"s" if len(winner) != 1 else ""} of {game}. Updated playcounts for {currentplayers}')

    if message.content.startswith('!help'):
        response = """\n
        Use "!stats playername (optional)gamename" to see stats for a player.  e.g. !stats breanna or !stats breanna,dakota sagrada,6 nimmt"\
        """
        await message.channel.send('"!players" to set active players.  e.g. "!players adam,breanna,caleb,dakota"')
        await message.channel.send('"!record winner,winner game" to record a game for all active players.  e.g. "!record Dakota Sagrada" or "!record Dakota,Breanna Codenames')
        await message.channel.send('''"!stats *name *game" to see stats.  If no game given, returns all.  If no name given, returns all players stats.\n
        e.g. "!stats Dakota Sagrada" or "!stats Breanna" or just "!stats"''')
        await message.channel.send('"!location name" to set location where game was played.  Defaults to "online"')
        await message.channel.send('"!info" to show current players, location, and if your database is on the current version.')
        await message.channel.send('"!updatedb" to update your database to the current version, if needed.')
        await message.channel.send('"**DANGEROUS** !delete where what" where = game,player what=what,to,delete WILL **DELETE** INFO FROM DB!')
    
    if message.content.startswith('!stats'):
        try:
            currentplayers = str(message.content).split(' ',2)[1].replace(' ','').lower().split(',')
        except:
            base = table.all()
            currentplayers = []
            for person in base:
                currentplayers.append(person["name"])
        try:
            game = str(message.content).split(' ',2)[2].lower().split(',')
        except:
            game = "all"
        for currentplayer in currentplayers:
            await message.channel.send(player_stats(currentplayer,game))

    if message.content.startswith('!attendance'):
        try:
            currentplayers = str(message.content).split(' ',1)[1].replace(' ','').lower().split(',')
        except:
            base = table.all()
            currentplayers = []
            for person in base:
                currentplayers.append(person["name"])
        for player in currentplayers:
            await message.channel.send(get_attendance(player))

    if message.content.startswith('!location'):
        try:
            location = str(message.content).split(' ',1)[1].replace(' ','').lower()
        except:
            location = "online"
        await message.channel.send(set_location(location))

    if message.content.startswith('!updatedb'):
        await message.channel.send(updatedb())

    if message.content.startswith('!delete'):
        where = str(message.content).split(' ',2)[1].lower()
        what = str(message.content).split(' ',2)[2].lower().split(',')
        if where == "player" or where == "players": result = del_players(what)
        if where == "game" or where == "games": result = del_games(what)
        else: result = "Something went wrong. Retry command in the format !delete player/game names,to,remove"
        await message.channel.send(result)

    if message.content.startswith('!recalc'):
        await message.channel.send(recalc())

    if message.content.startswith('!info'):
        location = get_location()
        players = get_active_players()
        add = "Your database is up to date."
        try:
            dbversion = int(config.get(User.id =="config")["version"])
        except:
            dbversion = 0
        if dbversion < currentDBVersion:
            add = f"Your database is on version {dbversion}.  The current version is {currentDBVersion}.  Please run !updatedb\n"
        await message.channel.send(f"Active players: {players}\nLocation: {location}\n{add}")



client.run(os.getenv('TOKEN'))


