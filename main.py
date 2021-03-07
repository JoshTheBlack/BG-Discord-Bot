import discord
import os
from dotenv import load_dotenv
#from replit import db

load_dotenv()

client = discord.Client()

@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!hi'):
        user = str(message.author)
        await message.channel.send(f'Hello! {user.split("#",1)[0]}')
    
    if message.content.startswith('!players'):
        players = str(message.content).split(' ',1)[1].replace(' ','').split(',')
        print(players)

client.run(os.getenv('TOKEN'))