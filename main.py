import typing

import discord
from discord.ext import commands

from consts import BOT_API, WEIRD_GUYS_GUILD_ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
	print(f'Logged in as {bot.user}')

	weird_guys_guild = bot.get_guild(WEIRD_GUYS_GUILD_ID)
	for member in weird_guys_guild.members:
		print(member)


@bot.command()
async def test(ctx: commands.Context, *, member: typing.Union[discord.Member, str]):
	if isinstance(member, discord.Member):
		await ctx.reply(f"You are {member.nick}")
	else:
		await ctx.reply(f"Could not find user {member}")


# @client.event
# async def on_message(message: discord.Message):
# 	if message.author == client.user:
# 		return


bot.run(BOT_API)
