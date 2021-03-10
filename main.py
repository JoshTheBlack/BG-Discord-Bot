import discord
import os
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from datetime import datetime

load_dotenv()
db = TinyDB('db.json')
User = Query()
client = discord.Client()
# db Format { player.name : [ player.name, player.wins, player.plays, player.played = {"game" : {wins, plays}}, player.active, attendance = [date, date, date...] }

@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))

@client.event
async def on_message(message, db=db, User=User):
    def set_players(players):
        for player in players:
            if db.search(User.name == player):
                stored = db.get(User.name == str(player))
                stored["active"] = True
                db.upsert(stored, User.name == player)
            else:
                db.upsert({"name": player, "wins":0,"plays":0,"played": {},"active": True, "attendance": []}, User.name == player)
        print(db.all())

    def reset_players():
        players = db.all()
        for player in players:
            player["active"] = False
            db.upsert(player,User.name == player["name"])
        print(db.all())

    def get_active_players():
        activePlayers = []
        base = db.all()
        for player in base:
            if player["active"] == True:
                activePlayers.append(player["name"])
        return activePlayers

    def record_play(game, winner):
        players = db.all()
        for player in players:
            if player["active"] == True:
                player["plays"] += 1
                date = datetime.today().strftime('%Y-%m-%d')
                if date not in player["attendance"]:
                    player["attendance"].append(date)
                if game not in player["played"]:
                    player["played"][game] = {"wins" : 0, "plays" : 0}
                player["played"][game]["plays"] += 1
                if player["name"] in winner:
                    player["wins"] += 1
                    player["played"][game]["wins"] += 1
            db.upsert(player,User.name == player["name"])
        print(db.all())

    def player_stats(playername, game="all"):
        player = db.get(User.name == playername)
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
        player = db.get(User.name == playername)
        if player == None:
            return f'**{playername}** has **no** recorded game sessions.'
        return f'**{playername}** has attended **{len(player["attendance"])}** recorded game session{"s" if len(player["attendance"]) != 1 else ""}.\n{player["attendance"]}'

    if message.author == client.user:
        return
    
    if message.content.startswith('!hi'):
        user = str(message.author)
        await message.channel.send(f'Hello! {user.split("#",1)[0]}')
    
    if message.content.startswith('!players'):
        reset_players()
        players = str(message.content).split(' ',1)[1].replace(' ','').lower().split(',')
        set_players(players)
        await message.channel.send(f'Active players set to {*players,}')
        
    if message.content.startswith('!record'):
        winner = str(message.content).split(' ',2)[1].lower().split(',')
        game = str(message.content).split(' ',2)[2].lower()
        record_play(game,winner)
        currentplayers = get_active_players()
        await message.channel.send(f'Recorded {winner} as the winner(s) of {game}. Updated playcounts for {currentplayers}')

    if message.content.startswith('!help'):
        response = """Use "!players" to set active players.  e.g. "!players adam,breanna,caleb,dakota"\n
        Use "!record (comma-separated winner names), (comma-separated game names)" to record a game for all active players.  e.g. "!record Dakota Sagrada" \n
        Use "!stats playername (optional)gamename" to see stats for a player.  e.g. !stats breanna or !stats breanna,dakota sagrada,6 nimmt"
        """
        await message.channel.send(response)
    
    if message.content.startswith('!stats'):
        currentplayers = str(message.content).split(' ',2)[1].replace(' ','').lower().split(',')
        try:
            game = str(message.content).split(' ',2)[2].lower().split(',')
        except:
            game = "all"
        #stats = ""
        for currentplayer in currentplayers:
            #stats += player_stats(currentplayer,game)
            await message.channel.send(player_stats(currentplayer,game))

    if message.content.startswith('!attendance'):
        currentplayers = str(message.content).split(' ',1)[1].replace(' ','').lower().split(',')
        for player in currentplayers:
            await message.channel.send(get_attendance(player))

client.run(os.getenv('TOKEN'))