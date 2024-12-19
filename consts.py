import pathlib

import discord

with open("private.txt", "r") as private:
	BOT_API = private.read()

COMMAND_PREFIX = "!"

WEIRD_GUYS_GUILD_ID = 688195144943796294

IGNORED_MEMBERS = (
	"iamplankton8065",
	"ergergerg1159",
	"teachamantoafish3188",
	"bernieferdinand",
	"grandmofftarkin6912"
)

CWD = pathlib.Path.cwd()
DATA_DIR = CWD / "data"

NO_PING = discord.AllowedMentions(everyone=False, users=False, roles=False)

COLLECT_COLOUR = discord.Colour.teal()

HIT_COLOUR = discord.Colour.blue()
CRITICAL_HIT_COLOUR = discord.Colour.blurple()
MISS_COLOUR = discord.Colour.red()

STATS_COLOUR = discord.Colour.blurple()

SIGN_UP_COMMAND_NAME = "sign_up"
