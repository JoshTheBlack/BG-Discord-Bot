
from tinydb import TinyDB, Query

User = Query()

def player_stats(playername, table, game="all"):
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
