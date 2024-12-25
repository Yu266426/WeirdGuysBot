import pathlib

import discord

with open("private.txt", "r") as private:
	BOT_API = private.read()

COMMAND_PREFIX = "!"

WEIRD_GUYS_GUILD_ID = 688195144943796294
ANNOUNCEMENTS_CHANNEL_ID = 766380173787398144
WEIRD_BALLS_CHANNEL_ID = 1317762286198460416

IGNORED_MEMBERS = (
	"iamplankton8065",
	"ergergerg1159",
	"teachamantoafish3188",
	"bernieferdinand",
	"grandmofftarkin6912",
	"domeyboy"
)

CWD = pathlib.Path.cwd()
DATA_DIR = CWD / "data"

NO_PING = discord.AllowedMentions(everyone=False, users=False, roles=False)

COLLECT_COLOR = discord.Color.teal()

HIT_COLOR = discord.Color.blue()
CRITICAL_HIT_COLOR = discord.Color.from_rgb(136, 90, 209)
MISS_COLOR = discord.Color.red()

STATS_COLOR = discord.Color.blurple()
LEVEL_UP_COLOR = discord.Color.from_rgb(48, 191, 112)

TEAMS_COLOR = discord.Color.dark_gold()
HELP_COLOR = discord.Color.greyple()

GAME_OVER_COLOR = discord.Color.gold()

# Admin commands
SIGN_UP_COMMAND_NAME = "sign_up"
DISTRIBUTE_MEMBERS_COMMAND_NAME = "dist_members"

# General commands
COLLECT_COMMAND_NAME = "collect"
THROW_COMMAND_NAME = "throw"
LEADERBOARD_COMMAND_NAME = "leader"
STATS_COMMAND_NAME = "stats"
