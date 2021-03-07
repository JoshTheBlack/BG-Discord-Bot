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
    if message.author == client.user:
        return
    
    if message.content.startswith('!hi'):
        user = str(message.author)
        await message.channel.send(f'Hello! {user.split("#",1)[0]}')
    
    if message.content.startswith('!players'):
        players = str(message.content).split(' ',1)[1].replace(' ','').lower().split(',')
        for player in players:
            if db.search(User.name == player):
                stored = db.get(User.name == str(player))
                stored["active"] = True
            else:
                db.upsert({"name": player, "wins":0,"plays":0,"played": [],"active": True, "won":False}, User.name == player)




client.run(os.getenv('TOKEN'))