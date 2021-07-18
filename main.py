from discord.ext import commands
from discord.utils import get
import os
from dotenv import load_dotenv
from utils.dbhelpers import *

load_dotenv("cfg/.env")
currentDBVersion = 1

# db Format { "index" : { "name" : name, "wins": win counter, "plays": play counter, "played": {"game1" : {wins, plays}, "game2": {wins, plays}...}, attendance = [[date, location]...] }}
# conf db Format {"index" : {"id" : "config", "version": dbversion, "location": location, "players": [player1, ...]}}

bot = commands.Bot(command_prefix='!', help_command=None)

@bot.event
async def on_ready():
    print("Logged in as {0.user}".format(bot))

# @bot.command(pass_context=True)
# # @commands.has_role("Mod")
# async def addrole(ctx, user: discord.Member, role: discord.Role):
#     await user.add_roles(role)
#     await ctx.send(f"hey {ctx.author.name}, {user.name} has been given a role called {role.name}")
# client.run(os.getenv('TOKEN'))

@bot.command(pass_context=True)
async def players(ctx):
    players = str(ctx.message.content).split(' ',1)[1].replace(' ','').lower().split(',')
    set_players(ctx, players)
    await ctx.send(f'Players set to {*players,}')

@bot.command(pass_context=True)
async def record(ctx):
    winner = str(ctx.message.content).split(' ',2)[1].lower().split(',')
    game = str(ctx.message.content).split(' ',2)[2].lower()
    record_play(game,winner, ctx)
    currentplayers = get_active_players(ctx)
    await ctx.send(f'Recorded {winner} as the winner{"s" if len(winner) != 1 else ""} of {game}. Updated playcounts for {currentplayers}')

@bot.command(pass_context=True)
async def stats(ctx):
    table = db.table(ctx.guild.name)
    try:
        currentplayers = str(ctx.message.content).split(' ',2)[1].replace(' ','').lower().split(',')
    except:
        base = table.all()
        currentplayers = []
        for person in base:
            currentplayers.append(person["name"])
    try:
        games = str(ctx.message.content).split(' ',2)[2].lower().split(',')
    except:
        games = "all"
    for currentplayer in currentplayers:
        await ctx.send(player_stats(currentplayer,table, games))

@bot.command(pass_context=True)
async def attendance(ctx):
    table, _ = get_db(ctx)
    try:
        currentplayers = str(ctx.message.content).split(' ',1)[1].replace(' ','').lower().split(',')
    except:
        base = table.all()
        currentplayers = []
        for person in base:
            currentplayers.append(person["name"])
    for player in currentplayers:
        await ctx.send(get_attendance(player, table))

@bot.command(pass_context=True)
async def location(ctx):
    _, config = get_db(ctx)
    try:
        location = str(ctx.message.content).split(' ',1)[1].replace(' ','').lower()
    except:
        location = "online"
    await ctx.send(set_location(location, config))

@bot.command(pass_context=True)
async def updatedb(ctx):
    table, config = get_db(ctx)
    await ctx.send(update_db(table, config, currentDBVersion))

@bot.command(pass_context=True)
async def delete(ctx):
    table, _ = get_db(ctx)
    where = str(ctx.message.content).split(' ',2)[1].lower()
    what = str(ctx.message.content).split(' ',2)[2].lower().split(',')
    if where == "player" or where == "players": result = del_players(what, table)
    elif where == "game" or where == "games": result = del_games(what, table)
    else: result = "Something went wrong. Retry command in the format !delete player/game names,to,remove"
    await ctx.send(result)

@bot.command(pass_context=True)
async def recalc(ctx):
    table, _ = get_db(ctx)
    await ctx.send(recalculate(table))

@bot.command(pass_context=True)
async def info(ctx):
    _, config = get_db(ctx)
    location = get_location(config)
    players = get_active_players(ctx)
    add = "Your database is up to date."
    try:
        dbversion = int(config.get(User.id =="config")["version"])
    except:
        dbversion = 0
    if dbversion < currentDBVersion:
        add = f"Your database is on version {dbversion}.  The current version is {currentDBVersion}.  Please run !updatedb\n"
    await ctx.send(f"Active players: {players}\nLocation: {location}\n{add}")


@bot.command()
async def help(message):
    await message.channel.send('"!players" to set active players.  e.g. "!players adam,breanna,caleb,dakota"')
    await message.channel.send('"!record winner,winner game" to record a game for all active players.  e.g. "!record Dakota Sagrada" or "!record Dakota,Breanna Codenames')
    await message.channel.send('''"!stats *name *game" to see stats.  If no game given, returns all.  If no name given, returns all players stats.\n
    e.g. "!stats Dakota Sagrada" or "!stats Breanna" or just "!stats"''')
    await message.channel.send('"!location name" to set location where game was played.  Defaults to "online"')
    await message.channel.send('"!info" to show current players, location, and if your database is on the current version.')
    await message.channel.send('"!updatedb" to update your database to the current version, if needed.')
    await message.channel.send('"**DANGEROUS** !delete where what" where = game,player what=what,to,delete WILL **DELETE** INFO FROM DB!')


if __name__ == "__main__":
    bot.run(os.getenv('TOKEN'))

