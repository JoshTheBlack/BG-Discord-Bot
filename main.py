import discord
import os
from dotenv import load_dotenv
from tinydb import TinyDB, Query

load_dotenv()
db = TinyDB('db.json')
User = Query()
client = discord.Client()
# db Format { player.name : [ player.name, player.wins, player.plays, player.played, player.active ] }

class Player:
    def __init__(self, name, wins, plays, played):
        '''played is a list of games played'''
        self.name = name.lower()
        self.wins = wins
        self.plays = plays
        self.played = played

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
                db.upsert({"name": player, "wins":0,"plays":0,"played": [],"active": True, "won":False}, User.name == player)
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

    def record_play(game, winner):
        players = db.all()
        for player in players:
            if player["active"] == True:
                player["plays"] += 1
                if game not in player["played"]:
                    player["played"].append(game)
                if player["name"] == winner:
                    player["wins"] += 1
            db.upsert(player,User.name == player["name"])
        print(db.all())

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
        game = str(message.content).split(' ',1)[1].lower().split(',',1)[0]
        winner = str(message.content).split(' ',1)[1].lower().split(',',1)[1]
        record_play(game,winner)
        currentplayers = get_active_players()
        await message.channel.send(f'Recorded {winner} as the winner of {game}. Updated playcounts for {currentplayers}')





client.run(os.getenv('TOKEN'))